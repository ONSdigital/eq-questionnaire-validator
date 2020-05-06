import re
from collections import defaultdict

from eq_translations.survey_schema import SurveySchema

from app.validation import error_messages
from app.validation.answers import get_answer_validator
from app.validation.blocks import get_block_validator
from app.validation.metadata_validator import MetadataValidator
from app.validation.questionnaire_schema import (
    QuestionnaireSchema,
    has_default_route,
    is_contained_in_list,
    get_routing_when_list,
    find_duplicates,
)
from app.validation.questions import get_question_validator
from app.validation.validator import Validator


class QuestionnaireValidator(Validator):
    def __init__(self, schema_element=None):
        super().__init__(schema_element)

        self.questionnaire_schema = QuestionnaireSchema(schema_element)

    def validate(self):
        metadata_validator = MetadataValidator(
            self.schema_element["metadata"], self.schema_element["theme"]
        )
        metadata_validator.validate()

        self.errors += metadata_validator.errors

        self.validate_duplicates()
        self.validate_smart_quotes()

        sections = self.schema_element.get("sections", [])
        all_groups = [group for section in sections for group in section.get("groups")]

        numeric_answer_ranges = {}

        for section in self.questionnaire_schema.sections:
            self._validate_section(section)

            for group in section["groups"]:
                self._validate_group_routing_rules(group, all_groups)

                for skip_condition in group.get("skip_conditions", []):
                    self._validate_skip_condition(skip_condition, group)

                self._validate_blocks(
                    section["id"], group["id"], all_groups, numeric_answer_ranges
                )

        required_hub_section_ids = self.schema_element.get("hub", {}).get(
            "required_completed_sections", []
        )

        self._validate_required_section_ids(
            self.questionnaire_schema.section_ids, required_hub_section_ids
        )

    def _validate_section(self, section):
        section_repeat = section.get("repeat")

        if section_repeat:
            self._validate_list_exists(section_repeat["for_list"])
            self._validate_placeholder_object(section_repeat["title"], None)

        section_summary = section.get("summary")
        if section_summary:
            for item in section_summary.get("items", []):
                self._validate_list_exists(item.get("for_list"))

    def _validate_required_section_ids(self, section_ids, required_section_ids):

        for required_section_id in required_section_ids:
            if required_section_id not in section_ids:
                self.add_error(
                    'Required hub completed section "{}" defined in hub does not '
                    "appear in schema".format(required_section_id)
                )

    def _validate_group_routing_rules(self, group, all_groups):
        self.validate_routing_rules_have_default(
            group.get("routing_rules", []), group["id"]
        )

        for rule in group.get("routing_rules", []):
            self.validate_routing_rule_target(group["blocks"], "block", rule)
            self.validate_routing_rule_target(all_groups, "group", rule)
            self.validate_routing_rule(rule, group)

    def validate_block_routing_rules(self, block, group, all_groups):
        self.validate_routing_rules_have_default(
            block.get("routing_rules", []), block["id"]
        )

        for rule in block.get("routing_rules", []):
            self.validate_routing_rule_target(group["blocks"], "block", rule)
            self.validate_routing_rule_target(all_groups, "group", rule)
            self.validate_routing_rule(rule, block)

    # pylint: disable=too-complex
    def _validate_blocks(  # noqa: C901 pylint: disable=too-many-branches
        self, section_id, group_id, all_groups, numeric_answer_ranges
    ):
        section = self.questionnaire_schema.get_section(section_id)
        group = self.questionnaire_schema.get_group(group_id)

        for block in group.get("blocks"):
            if (
                section_id == self.schema_element["sections"][-1]["id"]
                and group_id == section["groups"][-1]["id"]
                and block["id"] == group["blocks"][-1]["id"]
            ):
                self.validate_block_is_submission(block)

            self.validate_block_routing_rules(block, group, all_groups)

            for skip_condition in block.get("skip_conditions", []):
                self._validate_skip_condition(skip_condition, block)

            block_validator = get_block_validator(block, self.questionnaire_schema)
            block_validator.validate()
            self.errors += block_validator.errors

            self._validate_questions(block, numeric_answer_ranges)

            valid_metadata_ids = []
            if "metadata" in self.schema_element:
                valid_metadata_ids = [
                    m["name"] for m in self.schema_element["metadata"]
                ]

            source_references = self.questionnaire_schema.get_block_key_context(
                block["id"], "identifier"
            )

            self._validate_source_references(
                source_references, valid_metadata_ids, block["id"]
            )
            self._validate_placeholders(block["id"])
            self._validate_variants(block, numeric_answer_ranges)

    def _validate_questions(self, block_or_variant, numeric_answer_ranges):
        questions = block_or_variant.get("questions", [])
        question = block_or_variant.get("question")
        routing_rules = block_or_variant.get("routing_rules", {})
        default_route = has_default_route(routing_rules)

        if question:
            questions.append(question)

        for question in questions:
            question_validator = get_question_validator(question)
            question_validator.validate()

            self.errors += question_validator.errors

            for answer in question.get("answers", []):
                if routing_rules:
                    self.validate_default_route(answer, default_route)
                    self._validate_routing_on_answer_options(answer, routing_rules)

                answer_validator = get_answer_validator(
                    answer,
                    self.questionnaire_schema.list_names,
                    self.questionnaire_schema.block_ids,
                )

                answer_validator.validate()

                if answer["type"] in ["Number", "Currency", "Percentage"]:
                    numeric_answer_ranges[
                        answer["id"]
                    ] = answer_validator.get_numeric_range_values(numeric_answer_ranges)

                    answer_validator.validate_numeric_answer_types(
                        numeric_answer_ranges
                    )

                if question.get("summary") and answer["type"] != "TextField":
                    self.add_error(
                        error_messages.SUMMARY_HAS_NON_TEXTFIELD_ANSWER,
                        answer_id=answer["id"],
                    )
                self.errors += answer_validator.errors

    def validate_default_route(self, answer, has_default_route):
        if answer["mandatory"] and not has_default_route:
            default_route_not_defined = "Default route not defined for optional question [{}]".format(
                answer["id"]
            )
            self.errors.append(default_route_not_defined)

    def _validate_routing_on_answer_options(self, answer, routing_rules):
        answer_options = answer.get("options", [])
        option_values = [option["value"] for option in answer_options]
        routing_when_list = get_routing_when_list(routing_rules)

        if answer_options:
            for when_clause in routing_when_list:
                for when in when_clause.get("when", []):
                    if (
                        when
                        and when.get("id", "") == answer["id"]
                        and when.get("value", "") in option_values
                    ):
                        option_values.remove(when["value"])
                    else:
                        option_values = []

            has_unrouted_options = option_values and len(option_values) != len(
                answer_options
            )

            if has_unrouted_options and not has_default_route(routing_rules):
                self.errors.append(
                    "Routing rule not defined for answer [{}] missing options {}".format(
                        answer["id"], option_values
                    )
                )

    def _ensure_relevant_variant_fields_are_consistent(self, block, variants):
        """ Ensure consistency between relevant fields in variants

        - Ensure that question_ids are the same across all variants.
        - Ensure answer_ids are the same across all variants.
        - Ensure question types are the same across all variants.
        - Ensure answer types are the same across all variants.
        - Ensure default answers are the same across all variants.
        """
        if not variants:
            return

        results = self._get_question_variant_fields_sets(variants)

        if len(results["number_of_answers"]) > 1:
            self.add_error(
                "Variants in block: {} contain different numbers of answers".format(
                    block["id"]
                )
            )

        if len(results["question_ids"]) != 1:
            self.add_error(
                "Variants contain more than one question_id for block: {}. Found ids: {}".format(
                    block["id"], results["question_ids"]
                )
            )

        if len(results["question_types"]) != 1:
            self.add_error(
                "Variants have more than one question type for block: {}. Found types: {}".format(
                    block["id"], results["question_types"]
                )
            )

        if len(results["default_answers"]) > 1:
            self.add_error(
                "Variants contain different default answers for block: {}. Found ids: {}".format(
                    block["id"], results["question_ids"]
                )
            )

        if len(results["answer_ids"]) != next(iter(results["number_of_answers"])):
            self.add_error(
                "Variants have mismatched answer_ids for block: {}. Found ids: {}.".format(
                    block["id"], results["answer_ids"]
                )
            )

        for answer_id, type_set in results["answer_types"].items():
            if len(type_set) != 1:
                self.add_error(
                    "Variants have mismatched answer types for block: {}. Found types: {} for answer ID: {}.".format(
                        block["id"], type_set, answer_id
                    )
                )

    @staticmethod
    def _get_question_variant_fields_sets(variants):
        results = {
            "question_ids": set(),
            "question_types": set(),
            "answer_ids": set(),
            "answer_types": defaultdict(set),
            "default_answers": set(),
            "number_of_answers": set(),
        }

        for variant in variants:
            question_variant = variant["question"]
            results["question_ids"].add(question_variant["id"])
            results["question_types"].add(question_variant["type"])

            for answer in question_variant["answers"]:
                results["answer_ids"].add(answer["id"])
                results["answer_types"][answer["id"]].add(answer["type"])
                results["default_answers"].add(answer.get("default"))

            results["number_of_answers"].add(len(results["answer_ids"]))

        return results

    def _validate_variants(self, block, numeric_answer_ranges):
        question_variants = block.get("question_variants", [])
        content_variants = block.get("content_variants", [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            self._validate_questions(variant, numeric_answer_ranges)

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            self.add_error(
                "Variants contains fewer than two variants - block: {}".format(
                    block["id"]
                )
            )

        for variant in all_variants:
            self._validate_when_rule(variant.get("when", []), block["id"])

        self._ensure_relevant_variant_fields_are_consistent(block, question_variants)

    def validate_routing_rule_target(self, dict_list, goto_key, rule):
        if "goto" in rule and goto_key in rule["goto"].keys():
            referenced_id = rule["goto"][goto_key]

            if not is_contained_in_list(dict_list, referenced_id):
                invalid_block_error = "Routing rule routes to invalid {} [{}]".format(
                    goto_key, referenced_id
                )
                self.add_error(invalid_block_error)

    def validate_routing_rules_have_default(self, rules, block_or_group_id):
        """
        Ensure that a set of routing rules contains a default, without a when clause.
        """

        if rules and all(("goto" in rule for rule in rules)):
            default_routing_rule_count = 0

            for rule in rules:
                rule_directive = rule.get("goto")
                if rule_directive and "when" not in rule_directive:
                    default_routing_rule_count += 1

            if not default_routing_rule_count:
                self.add_error(
                    f"The routing rules for group or block: {block_or_group_id} "
                    f"must contain a default routing rule without a when rule"
                )
            elif default_routing_rule_count > 1:
                self.add_error(
                    f"The routing rules for group or block: {block_or_group_id} "
                    f"contain multiple default routing rules. Some of them will not be used"
                )

    def validate_routing_rule(self, rule, block_or_group):
        rule = rule.get("goto")
        if "when" in rule:
            self._validate_when_rule(rule["when"], block_or_group["id"])

    def validate_answer_value_in_when_rule(self, when_rule):
        when_values = when_rule.get("values", [])
        when_value = when_rule.get("value")
        if when_value:
            when_values.append(when_value)

        option_values = self.questionnaire_schema.answer_id_to_option_values_map.get(
            when_rule["id"]
        )
        if not option_values:
            return []

        for value in when_values:
            if value not in option_values:
                self.add_error(
                    error_messages.INVALID_WHEN_RULE_ANSWER_VALUE,
                    answer_id=when_rule["id"],
                    value=value,
                )

    def _validate_skip_condition(self, skip_condition, block_or_group):
        """
        Validate skip condition is valid
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        when = skip_condition.get("when")

        self._validate_when_rule(when, block_or_group["id"])

    def _validate_primary_person_list_answer_references(self, block):

        main_block_questions = self.questionnaire_schema.get_all_questions_for_block(
            block
        )
        main_block_ids = {
            answer["id"]
            for question in main_block_questions
            for answer in question["answers"]
        }

        if block["add_or_edit_answer"]["id"] not in main_block_ids:
            self.add_error(
                error_messages.ADD_OR_EDIT_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK,
                referenced_id=block["add_or_edit_answer"]["id"],
            )

    def _validate_when_rule(self, when_clause, referenced_id):
        """
        Validates any answer id in a when clause exists within the schema
        Will also check that comparison exists
        """
        for when in when_clause:
            if "list" in when:
                self._validate_list_name_in_when_rule(when)
                break

            valid_answer_ids = self.validate_answer_ids_present_in_schema(
                when, referenced_id
            )
            if not valid_answer_ids:
                break

            # We know the ids are correct, so can continue to perform validation
            self._validate_checkbox_exclusive_conditions_in_when_rule(when)

            if "comparison" in when:
                self._validate_comparison_in_when_rule(when, referenced_id)

            if "id" in when:
                self.validate_answer_value_in_when_rule(when)

    def validate_answer_ids_present_in_schema(self, when, referenced_id):
        """
        Validates that any ids that are referenced within the when rule are present within the schema.  This prevents
        writing when conditions against id's that don't exist.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        ids_to_check = []

        if "id" in when:
            ids_to_check.append(("id", when["id"]))
        if "comparison" in when and when["comparison"]["source"] == "answers":
            ids_to_check.append(("comparison.id", when["comparison"]["id"]))

        for key, present_id in ids_to_check:
            if present_id not in self.questionnaire_schema.answers_with_context:
                self.add_error(
                    error_messages.NON_EXISTENT_WHEN_KEY,
                    answer_id=present_id,
                    key=key,
                    referenced_id=referenced_id,
                )
                return False
        return True

    def _validate_checkbox_exclusive_conditions_in_when_rule(self, when):
        """
        Validate checkbox exclusive conditions are only used when answer type is Checkbox
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        condition = when["condition"]
        checkbox_exclusive_conditions = (
            "contains any",
            "contains all",
            "contains",
            "not contains",
        )
        all_checkbox_conditions = checkbox_exclusive_conditions + ("set", "not set")
        answer_type = (
            self.questionnaire_schema.answers_with_context[when["id"]]["answer"]["type"]
            if "id" in when
            else None
        )

        if answer_type == "Checkbox":
            if condition not in all_checkbox_conditions:
                answer_id = self.questionnaire_schema.answers_with_context[when["id"]][
                    "answer"
                ]["id"]
                self.add_error(
                    error_messages.CHECKBOX_MUST_USE_CORRECT_CONDITION,
                    condition=condition,
                    answer_id=answer_id,
                )
        elif condition in checkbox_exclusive_conditions:
            answer_id = self.questionnaire_schema.answers_with_context[when["id"]][
                "answer"
            ]["id"]
            self.add_error(
                f"The condition `{condition}` can only be used with"
                " `Checkbox` answer types. "
                f"Found answer type: {answer_type} ({answer_id})."
            )

    def _validate_comparison_in_when_rule(self, when, referenced_id):
        """
        Validate that conditions requiring list match values define a comparison answer id that is of type Checkbox
        and ensure all other conditions with comparison id match answer types
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        if when["comparison"]["source"] == "answers":
            answer_id, comparison_id, condition = (
                when["id"],
                when["comparison"]["id"],
                when["condition"],
            )
            comparison_answer_type = self.questionnaire_schema.answers_with_context[
                comparison_id
            ]["answer"]["type"]
            id_answer_type = self.questionnaire_schema.answers_with_context[answer_id][
                "answer"
            ]["type"]
            conditions_requiring_list_match_values = (
                "equals any",
                "not equals any",
                "contains any",
                "contains all",
            )

            if condition in conditions_requiring_list_match_values:
                if comparison_answer_type != "Checkbox":
                    self.add_error(
                        error_messages.NON_CHECKBOX_COMPARISON_ID,
                        comparison_id=comparison_id,
                        condition=condition,
                    )

            elif comparison_answer_type != id_answer_type:
                self.add_error(
                    error_messages.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
                    comparison_id=comparison_id,
                    answer_id=answer_id,
                    referenced_id=referenced_id,
                )

    def _validate_list_name_in_when_rule(self, when):
        """
        Validate that the list referenced in the when rule is defined in the schema
        """
        list_name = when["list"]
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.LIST_REFERENCE_INVALID, list_name=list_name)

    def validate_duplicates(self):
        for duplicate in find_duplicates(self.questionnaire_schema.ids):
            self.add_error("Duplicate id found", id=duplicate)

    def validate_block_is_submission(self, last_block):
        """
        Validate that the final block is of type Summary or Confirmation.
        :param last_block: The final block in the schema
        :return: List of dictionaries containing error messages, otherwise it returns an empty list
        """
        is_last_block_valid = last_block["type"] in {"Summary", "Confirmation"}

        if is_last_block_valid and self.questionnaire_schema.is_hub_enabled:
            self.add_error(error_messages.QUESTIONNAIRE_ONLY_ONE_PAGE)

        if not is_last_block_valid and not self.questionnaire_schema.is_hub_enabled:
            self.add_error(error_messages.QUESTIONNAIRE_MUST_CONTAIN_PAGE)

    def _validate_referred_numeric_answer(self, answer, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        if answer_ranges[answer.get("id")]["min"] is None:
            error_message = 'The referenced answer "{}" can not be used to set the minimum of answer "{}"'.format(
                answer["minimum"]["value"]["identifier"], answer["id"]
            )
            self.add_error(error_message)
        if answer_ranges[answer.get("id")]["max"] is None:
            error_message = 'The referenced answer "{}" can not be used to set the maximum of answer "{}"'.format(
                answer["maximum"]["value"]["identifier"], answer["id"]
            )
            self.add_error(error_message)

    def _validate_placeholder_object(self, placeholder_object, current_block_id):
        """ Current block id may be None if called outside of a block
        """
        placeholders_in_string = set()
        placeholder_regex = re.compile("{(.*?)}")
        if "text" in placeholder_object:
            placeholders_in_string.update(
                placeholder_regex.findall(placeholder_object.get("text"))
            )
        elif "text_plural" in placeholder_object:
            for text in placeholder_object["text_plural"]["forms"].values():
                placeholders_in_string.update(placeholder_regex.findall(text))

        placeholder_definition_names = set()
        for placeholder_definition in placeholder_object.get("placeholders"):
            placeholder_definition_names.add(placeholder_definition["placeholder"])

            transforms = placeholder_definition.get("transforms")
            if transforms:
                self._validate_placeholder_transforms(transforms, current_block_id)

        placeholder_differences = placeholders_in_string - placeholder_definition_names

        if placeholder_differences:
            try:
                text = placeholder_object["text"]
            except KeyError:
                text = placeholder_object["text_plural"]["forms"]["other"]

            self.add_error(
                error_messages.PLACEHOLDERS_DONT_MATCH_DEFINITIONS,
                text=text,
                differences=placeholder_differences,
            )

    def _validate_placeholders(self, block_id):
        strings_with_placeholders = self.questionnaire_schema.get_block_key_context(
            block_id, "placeholders"
        )
        for placeholder_object in strings_with_placeholders:
            self._validate_placeholder_object(placeholder_object, block_id)

    def _validate_source_references(
        self, source_references, valid_metadata_ids, block_id
    ):
        for source_reference in source_references:
            source = source_reference["source"]
            if isinstance(source_reference["identifier"], str):
                identifiers = [source_reference["identifier"]]
            else:
                identifiers = source_reference["identifier"]

            if source == "answers":
                self.validate_answer_source_reference(identifiers, block_id)

            elif source == "metadata":
                self._validate_metadata_source_reference(
                    identifiers, valid_metadata_ids, block_id
                )

            elif source == "list":
                self._validate_list_source_reference(identifiers, block_id)

    def validate_answer_source_reference(self, identifiers, current_block_id):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.answers_with_context:
                self.add_error(
                    error_messages.ANSWER_REFERENCE_INVALID,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )
            elif (
                self.questionnaire_schema.answers_with_context[identifier]["block"]
                == current_block_id
            ):
                self.add_error(
                    error_messages.ANSWER_SELF_REFERENCE,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )

    def _validate_metadata_source_reference(
        self, identifiers, valid_metadata_ids, current_block_id
    ):
        for identifier in identifiers:
            if identifier not in valid_metadata_ids:
                self.add_error(
                    error_messages.METADATA_REFERENCE_INVALID,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )

    def _validate_list_source_reference(self, identifiers, current_block_id):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.list_names:
                self.add_error(
                    error_messages.LIST_REFERENCE_INVALID,
                    id=identifier,
                    block_id=current_block_id,
                )

    def _validate_list_exists(self, list_name):
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

    def _validate_placeholder_transforms(self, transforms, block_id):
        # First transform can't reference a previous transform
        first_transform = transforms[0]
        for argument_name in first_transform.get("arguments"):
            argument = first_transform["arguments"][argument_name]
            if (
                isinstance(argument, dict)
                and argument.get("source") == "previous_transform"
            ):
                self.add_error(
                    error_messages.FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF,
                    block_id=block_id,
                )

        # Previous transform must be referenced in all subsequent transforms
        for transform in transforms[1:]:
            previous_transform_used = False
            for argument_name in transform.get("arguments"):
                argument = transform["arguments"][argument_name]
                if (
                    isinstance(argument, dict)
                    and argument.get("source") == "previous_transform"
                ):
                    previous_transform_used = True

            if not previous_transform_used:
                self.add_error(
                    error_messages.NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN, block_id=block_id
                )

    def validate_smart_quotes(self):

        schema_object = SurveySchema(self.schema_element)

        # pylint: disable=invalid-string-quote
        quote_regex = re.compile(r"['|\"]+(?![^{]*})+(?![^<]*>)")

        for translatable_item in schema_object.translatable_items:
            schema_text = translatable_item.value

            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for schema_text in values_to_check:
                found = quote_regex.search(schema_text)

                if found:
                    self.add_error(
                        error_messages.DUMB_QUOTES_FOUND,
                        pointer=translatable_item.pointer,
                    )
