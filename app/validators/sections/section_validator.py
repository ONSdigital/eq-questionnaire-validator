"""This code defines a SectionValidator class that validates a section schema element in a questionnaire."""

from collections import defaultdict

from app import error_messages
from app.validators.answers import get_answer_validator
from app.validators.blocks import get_block_validator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    get_object_containing_key,
)
from app.validators.questions import get_question_validator
from app.validators.routing.routing_validator import RoutingValidator
from app.validators.rules.rule_validator import RulesValidator
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


class SectionValidator(Validator):
    """Validates a section schema element."""

    def __init__(self, schema_element, questionnaire_schema):
        """Initializes the SectionValidator."""
        super().__init__(schema_element)
        self.section = schema_element
        self.questionnaire_schema = questionnaire_schema
        self.context["section_id"] = self.section["id"]

    def validate(self):
        """Validates the section schema element."""
        self.validate_repeat()
        self.validate_value_sources()
        if self.errors:  # return when value sources are not valid
            return self.errors
        self.validate_summary()
        self.validate_groups()
        self.validate_section_enabled()
        self.validate_number_of_list_collectors()
        self.validate_section_summary_items()
        return self.errors

    def validate_repeat(self):
        """Validates the repeat conditions for a section."""
        section_repeat = self.section.get("repeat", None)

        if section_repeat:
            self.validate_list_exists(section_repeat["for_list"])

    def validate_summary(self):
        """Validates the summary for a section.

        We validate here: if there is a summary without items or there is no summary or there is a list summary
        within a section then we allow multiple list collectors otherwise we disallow them.
        """
        if not (section_summary := self.section.get("summary")):
            return

        if section_summary.get("items", []):
            self._validate_multiple_list_collectors()
            for item in section_summary.get("items", []):
                self.validate_list_exists(item.get("for_list"))

    def validate_section_enabled(self):
        """Validates the enabled condition for a section."""
        section_enabled = self.section.get("enabled", None)
        if not section_enabled:
            return

        when = section_enabled["when"]
        when_validator = RulesValidator(
            when,
            self.section["id"],
            self.questionnaire_schema,
        )
        self.errors += when_validator.validate()

    def validate_list_exists(self, list_name):
        """Validates that a list exists in the questionnaire schema."""
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

    def validate_skip_conditions(self, skip_condition, origin_id):
        """Validates the skip conditions for a schema element."""
        when_validator = RulesValidator(
            skip_condition["when"],
            origin_id,
            self.questionnaire_schema,
        )
        self.errors += when_validator.validate()

    def validate_value_sources(self):
        """Validates the value sources in a section."""
        source_references = get_object_containing_key(self.section, "identifier")
        for json_path, source_reference, parent_block in source_references:
            if "source" in source_reference:
                value_source_validator = ValueSourceValidator(
                    value_source=source_reference,
                    json_path=json_path,
                    questionnaire_schema=self.questionnaire_schema,
                    parent_section=self.section,
                    parent_block=parent_block,
                )
                self.errors += value_source_validator.validate()

    def validate_groups(self):
        """Validates the groups in a section."""
        for group in self.section["groups"]:
            self.validate_routing(group, group)
            self.validate_blocks(group["id"])

    def validate_blocks(self, group_id):
        """Validates the blocks in a group."""
        group = self.questionnaire_schema.get_group(group_id)

        for block in group.get("blocks"):
            self.validate_routing(block, group)

            block_validator = get_block_validator(block, self.questionnaire_schema)
            self.errors += block_validator.validate()

            self.validate_question(block)
            self.validate_variants(block)
            self.validate_repeating_blocks(block)

    def validate_routing(self, schema_element, group):
        """Validates the routing rules for a schema element."""
        if "routing_rules" in schema_element:
            routing_validator = RoutingValidator(
                routing_rules=schema_element["routing_rules"],
                group=group,
                origin_id=schema_element["id"],
                questionnaire_schema=self.questionnaire_schema,
            )
            self.errors += routing_validator.validate()
        if skip_conditions := schema_element.get("skip_conditions"):
            self.validate_skip_conditions(skip_conditions, schema_element["id"])

    def validate_question(self, block_or_variant):
        """Validates the question in a block or variant."""
        question = block_or_variant.get("question")

        if question:
            question_validator = get_question_validator(
                question,
                self.questionnaire_schema,
            )

            self.errors += question_validator.validate()

            self._validate_answers(question)

    def validate_variants(self, block):
        """Validates the variants of a block."""
        question_variants = block.get("question_variants", [])
        content_variants = block.get("content_variants", [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            self.validate_question(variant)

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            self.add_error(
                error_messages.VARIANTS_HAS_ONE_VARIANT,
                block_id=block["id"],
            )

        for variant in all_variants:
            if when_clause := variant.get("when"):
                when_validator = RulesValidator(
                    when_clause,
                    self.section["id"],
                    self.questionnaire_schema,
                )
                self.errors += when_validator.validate()

        self.validate_variant_fields(block, question_variants)

    def validate_variant_fields(self, block, variants):
        """Ensure consistency between relevant fields in variants.

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
                error_messages.VARIANTS_HAVE_DIFFERENT_ANSWER_LIST_LENGTHS,
                block_id=block["id"],
            )

        if len(results["question_ids"]) != 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_DIFFERENT_QUESTION_IDS,
                block_id=block["id"],
                question_ids=results["question_ids"],
            )

        if len(results["question_types"]) != 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_MULTIPLE_QUESTION_TYPES,
                block_id=block["id"],
                question_types=results["question_types"],
            )

        if len(results["default_answers"]) > 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_DIFFERENT_DEFAULT_ANSWERS,
                block_id=block["id"],
                question_ids=results["question_ids"],
            )

        if len(results["answer_ids"]) != next(iter(results["number_of_answers"])):
            self.add_error(
                error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_IDS,
                block_id=block["id"],
                answer_ids=results["answer_ids"],
            )

        for answer_id, type_set in results["answer_types"].items():
            if len(type_set) != 1:
                self.add_error(
                    error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_TYPES,
                    block_id=block["id"],
                    answer_types=type_set,
                    answer_id=answer_id,
                )

    def validate_repeating_blocks(self, block):
        """Validates the repeating blocks in the section."""
        # Repeating blocks must be validated here instead of from ListCollectorValidator
        # as the latter cannot do standard block validation
        for repeating_block in block.get("repeating_blocks", []):
            block_validator = get_block_validator(
                repeating_block,
                self.questionnaire_schema,
            )
            self.errors += block_validator.validate()

            self.validate_question(repeating_block)
            self.validate_variants(repeating_block)

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

        # Code to handle comparison of variants which contain a MutuallyExclusive answer type
        if (
            len(results["question_types"]) > 1
            and "MutuallyExclusive" in results["question_types"]
        ):
            results["question_types"].remove("MutuallyExclusive")

            results["answer_ids"].clear()

            results["number_of_answers"].clear()

            for variant in variants:
                if variant["question"]["type"] == "MutuallyExclusive":
                    non_exclusive_answer = variant["question"]["answers"][0]
                    results["answer_ids"].add(non_exclusive_answer["id"])
                else:
                    for answer in variant["question"]["answers"]:
                        results["answer_ids"].add(answer["id"])

                results["number_of_answers"].add(len(results["answer_ids"]))

        return results

    def validate_number_of_list_collectors(self):
        """Validates the number of list collectors in the section."""
        if (
            self.has_list_summary_with_non_item_answers()
            and self.has_multiple_list_collectors()
        ):
            self.add_error(error_messages.MULTIPLE_LIST_COLLECTORS)

    def has_list_summary_with_non_item_answers(self):
        """Checks if the list summary shows non-item answers."""
        if summary := self.schema_element.get("summary"):
            show_non_item_answers = summary.get("show_non_item_answers")
            return summary.get("items") and show_non_item_answers

    def has_multiple_list_collectors(self):
        """Checks if there are multiple list collectors in the section."""
        list_collectors = []
        for group in self.schema_element.get("groups"):
            list_collectors.extend(
                block
                for block in group.get("blocks")
                if block["type"] in ["ListCollector"]
            )

        return len(list_collectors) > 1

    def validate_section_summary_items(self):
        """Validates the summary items in the section."""
        summary_items = self.schema_element.get("summary", {}).get("items", [])
        if not summary_items:
            return

        blocks = self.questionnaire_schema.get_blocks(type="ListCollector")
        list_collector_answer_ids_by_list = defaultdict(list)
        for block in blocks:
            list_collector_answer_ids_by_list[block["for_list"]].extend(
                self.questionnaire_schema.get_list_collector_answer_ids(block["id"]),
            )

        for item in summary_items:
            list_collector_answer_ids_for_list = list_collector_answer_ids_by_list[
                item["for_list"]
            ]

            if item_anchor_answer_id := item.get("item_anchor_answer_id"):
                self._validate_item_anchor_answer_id_belongs_to_list_collector(
                    item_anchor_answer_id,
                    list_collector_answer_ids_for_list,
                    item["for_list"],
                )

            for answer_source in item.get("related_answers", []):
                self._validate_related_answer_belong_to_list_collector(
                    answer_source,
                    list_collector_answer_ids_for_list,
                )
                self._validate_related_answer_has_label(answer_source)

    def _validate_related_answer_belong_to_list_collector(
        self,
        answer_source,
        list_collector_answer_ids,
    ):
        if answer_source["identifier"] not in list_collector_answer_ids:
            self.add_error(
                error_messages.RELATED_ANSWERS_NOT_IN_LIST_COLLECTOR,
                id=answer_source["identifier"],
            )

    def _validate_item_anchor_answer_id_belongs_to_list_collector(
        self,
        anchor_answer_id,
        list_collector_answer_ids,
        list_name,
    ):
        if anchor_answer_id not in list_collector_answer_ids:
            self.add_error(
                error_messages.ITEM_ANCHOR_ANSWER_ID_NOT_IN_LIST_COLLECTOR.format(
                    answer_id=anchor_answer_id,
                    list_name=list_name,
                ),
                id=anchor_answer_id,
            )

    def _validate_related_answer_has_label(self, answer_source):
        answer = self.questionnaire_schema.get_answer(answer_source["identifier"])
        if not answer.get("label"):
            self.add_error(
                error_messages.NO_LABEL_FOR_RELATED_ANSWER.format(
                    answer_id=answer_source["identifier"],
                ),
                id=answer_source["identifier"],
            )

    def _validate_answers(self, question):
        for answer in QuestionnaireSchema.get_answers_from_question(question):
            answer_validator = get_answer_validator(answer, self.questionnaire_schema)

            answer_validator.validate()

            if question.get("summary") and answer["type"] not in [
                "TextField",
                "Checkbox",
                "Number",
            ]:
                self.add_error(
                    error_messages.UNSUPPORTED_QUESTION_SUMMARY_ANSWER_TYPE,
                    answer_id=answer["id"],
                )
            self.errors += answer_validator.errors

    def _validate_multiple_list_collectors(self):
        for_lists = []

        for block_id in self.questionnaire_schema.get_section_block_ids(
            self.section["id"],
        ):
            block = self.questionnaire_schema.get_block(block_id)
            if block["type"] in ["ListCollector", "ListCollectorContent"]:
                # Validation of two list collectors for the same list is disabled if summary is enabled
                if block.get("summary"):
                    break
                # Two list collectors for different lists in the same section are allowed
                if block["for_list"] not in for_lists:
                    for_lists.append(block["for_list"])

                else:
                    self.add_error(
                        error_messages.MULTIPLE_LIST_COLLECTORS_WITH_SUMMARY_ENABLED,
                        for_list=block["for_list"],
                    )
