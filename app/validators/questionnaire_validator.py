import re
from collections import defaultdict

from eq_translations.survey_schema import SurveySchema

from app import error_messages
from app.validators.answers import get_answer_validator, NumberAnswerValidator
from app.validators.blocks import get_block_validator
from app.validators.metadata_validator import MetadataValidator
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    has_default_route,
    find_duplicates,
)
from app.validators.questions import get_question_validator
from app.validators.routing.answer_routing_validator import AnswerRoutingValidator
from app.validators.routing.routing_validator import RoutingValidator

from app.validators.routing.when_validator import WhenValidator
from app.validators.validator import Validator


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

        numeric_answer_ranges = {}

        for section in self.questionnaire_schema.sections:
            self.validate_section(section)

            for group in section["groups"]:
                group_routing_validator = RoutingValidator(
                    group, group, self.questionnaire_schema
                )
                group_routing_validator.validate()
                self.errors += group_routing_validator.errors

                self.validate_blocks(section["id"], group["id"], numeric_answer_ranges)

        required_hub_section_ids = self.schema_element.get("hub", {}).get(
            "required_completed_sections", []
        )

        self.validate_required_section_ids(
            self.questionnaire_schema.section_ids, required_hub_section_ids
        )

    def validate_section(self, section):
        section_repeat = section.get("repeat")

        if section_repeat:
            self.validate_list_exists(section_repeat["for_list"])
            placeholder_validator = PlaceholderValidator(
                section, self.questionnaire_schema
            )
            placeholder_validator.validate_placeholder_object(
                section_repeat["title"], None
            )
            self.errors += placeholder_validator.errors

        section_summary = section.get("summary")

        if section_summary:
            for item in section_summary.get("items", []):
                self.validate_list_exists(item.get("for_list"))

    def validate_required_section_ids(self, section_ids, required_section_ids):

        for required_section_id in required_section_ids:
            if required_section_id not in section_ids:
                self.add_error(
                    error_messages.REQUIRED_HUB_SECTION_UNDEFINED,
                    required_section_id=required_section_id,
                )

    def validate_blocks(self, section_id, group_id, numeric_answer_ranges):
        section = self.questionnaire_schema.get_section(section_id)
        group = self.questionnaire_schema.get_group(group_id)

        for block in group.get("blocks"):
            if (
                section_id == self.schema_element["sections"][-1]["id"]
                and group_id == section["groups"][-1]["id"]
                and block["id"] == group["blocks"][-1]["id"]
            ):
                self.validate_block_is_submission(block)

            block_routing_validator = RoutingValidator(
                block, group, self.questionnaire_schema
            )
            block_routing_validator.validate()
            self.errors += block_routing_validator.errors

            block_validator = get_block_validator(block, self.questionnaire_schema)
            block_validator.validate()
            self.errors += block_validator.errors

            self.validate_questions(block, numeric_answer_ranges)
            self.validate_variants(block, numeric_answer_ranges)

    def validate_questions(self, block_or_variant, numeric_answer_ranges):
        questions = block_or_variant.get("questions", [])
        question = block_or_variant.get("question")
        routing_rules = block_or_variant.get("routing_rules", {})

        if question:
            questions.append(question)

        for question in questions:
            question_validator = get_question_validator(question)
            question_validator.validate()

            self.errors += question_validator.errors

            for answer in question.get("answers", []):
                if routing_rules:
                    answer_routing_validator = AnswerRoutingValidator(
                        answer, routing_rules
                    )
                    answer_routing_validator.validate()
                    self.errors += answer_routing_validator.errors

                answer_validator = get_answer_validator(
                    answer,
                    self.questionnaire_schema.list_names,
                    self.questionnaire_schema.block_ids,
                )

                answer_validator.validate()

                if isinstance(answer_validator, NumberAnswerValidator):
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

    def validate_variant_fields(self, block, variants):
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

    def validate_variants(self, block, numeric_answer_ranges):
        question_variants = block.get("question_variants", [])
        content_variants = block.get("content_variants", [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            self.validate_questions(variant, numeric_answer_ranges)

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            self.add_error(
                error_messages.VARIANTS_HAS_ONE_VARIANT, block_id=block["id"]
            )

        for variant in all_variants:
            when_clause = variant.get("when", [])
            when_validator = WhenValidator(
                when_clause, block["id"], self.questionnaire_schema
            )
            when_validator.validate()
            self.errors += when_validator.errors

        self.validate_variant_fields(block, question_variants)

    def validate_primary_person_list_answer_references(self, block):
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

    def validate_duplicates(self):
        for duplicate in find_duplicates(self.questionnaire_schema.ids):
            self.add_error(error_messages.DUPLICATE_ID_FOUND, id=duplicate)

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

    def validate_referred_numeric_answer(self, answer, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        if answer_ranges[answer.get("id")]["min"] is None:
            self.add_error(
                error_messages.ANSWER_REFERENCE_CANNOT_BE_USED_ON_MIN,
                reference_id=answer["minimum"]["value"]["identifier"],
                answer_id=answer["id"],
            )
        if answer_ranges[answer.get("id")]["max"] is None:
            self.add_error(
                error_messages.ANSWER_REFERENCE_CANNOT_BE_USED_ON_MAX,
                reference_id=answer["maximum"]["value"]["identifier"],
                answer_id=answer["id"],
            )

    def validate_list_exists(self, list_name):
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

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
