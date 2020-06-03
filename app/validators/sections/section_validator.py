from collections import defaultdict

from app import error_messages
from app.validators.validator import Validator
from app.validators.questions import get_question_validator
from app.validators.routing.answer_routing_validator import AnswerRoutingValidator
from app.validators.routing.routing_validator import RoutingValidator
from app.validators.routing.when_rule_validator import WhenRuleValidator
from app.validators.answers import get_answer_validator
from app.validators.blocks import get_block_validator


class SectionValidator(Validator):
    QUESTIONNAIRE_MUST_CONTAIN_PAGE = (
        "Questionnaire must contain one of [Confirmation page, Summary page, Hub page]"
    )
    QUESTIONNAIRE_ONLY_ONE_PAGE = "Questionnaire can only contain one of [Confirmation page, Summary page, Hub page]"

    def __init__(self, schema_element, questionnaire_schema):
        super().__init__(schema_element)
        self.section = schema_element
        self.questionnaire_schema = questionnaire_schema
        self.context["section_id"] = self.section["id"]

    def validate(self):
        self.validate_repeat()
        self.validate_summary()
        self.validate_groups()
        return self.errors

    def validate_repeat(self):
        section_repeat = self.section.get("repeat", None)

        if section_repeat:
            self.validate_list_exists(section_repeat["for_list"])

    def validate_summary(self):
        section_summary = self.section.get("summary", None)

        if section_summary:
            for item in section_summary.get("items", []):
                self.validate_list_exists(item.get("for_list"))

    def validate_list_exists(self, list_name):
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

    def validate_groups(self):
        for group in self.section["groups"]:
            group_routing_validator = RoutingValidator(
                group, group, self.questionnaire_schema
            )
            self.errors += group_routing_validator.validate()

            self.validate_blocks(self.section["id"], group["id"])

    def validate_blocks(self, section_id, group_id):
        group = self.questionnaire_schema.get_group(group_id)

        last_section = self.questionnaire_schema.sections[-1]
        last_group = last_section["groups"][-1]
        last_block = last_group["blocks"][-1]

        for block in group.get("blocks"):
            if (
                section_id == last_section["id"]
                and group_id == last_group["id"]
                and block["id"] == last_block["id"]
            ):
                self.validate_block_is_submission(block)

            block_routing_validator = RoutingValidator(
                block, group, self.questionnaire_schema
            )
            self.errors += block_routing_validator.validate()

            block_validator = get_block_validator(block, self.questionnaire_schema)
            self.errors += block_validator.validate()

            self.validate_questions(block)
            self.validate_variants(block)

    def validate_block_is_submission(self, last_block):
        """
        Validate that the final block is of type Summary or Confirmation.
        :param last_block: The final block in the schema
        :return: List of dictionaries containing error messages, otherwise it returns an empty list
        """
        is_last_block_valid = last_block["type"] in {"Summary", "Confirmation"}

        if is_last_block_valid and self.questionnaire_schema.is_hub_enabled:
            self.add_error(self.QUESTIONNAIRE_ONLY_ONE_PAGE)

        if not is_last_block_valid and not self.questionnaire_schema.is_hub_enabled:
            self.add_error(self.QUESTIONNAIRE_MUST_CONTAIN_PAGE)

    def validate_questions(self, block_or_variant):
        questions = block_or_variant.get("questions", [])
        question = block_or_variant.get("question")
        routing_rules = block_or_variant.get("routing_rules", {})

        if question:
            questions.append(question)

        for question in questions:
            question_validator = get_question_validator(question)

            self.errors += question_validator.validate()

            for answer in question.get("answers", []):
                if routing_rules:
                    answer_routing_validator = AnswerRoutingValidator(
                        answer, routing_rules
                    )
                    self.errors += answer_routing_validator.validate()

                answer_validator = get_answer_validator(
                    answer, self.questionnaire_schema
                )

                answer_validator.validate()

                if question.get("summary") and answer["type"] != "TextField":
                    self.add_error(
                        error_messages.SUMMARY_HAS_NON_TEXTFIELD_ANSWER,
                        answer_id=answer["id"],
                    )
                self.errors += answer_validator.errors

    def validate_variants(self, block):
        question_variants = block.get("question_variants", [])
        content_variants = block.get("content_variants", [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            self.validate_questions(variant)

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            self.add_error(
                error_messages.VARIANTS_HAS_ONE_VARIANT, block_id=block["id"]
            )

        for variant in all_variants:
            when_clause = variant.get("when", [])
            when_validator = WhenRuleValidator(
                when_clause, block["id"], self.questionnaire_schema
            )
            self.errors += when_validator.validate()

        self.validate_variant_fields(block, question_variants)

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
