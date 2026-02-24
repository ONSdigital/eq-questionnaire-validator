"""This module contains the CalculatedSummaryBlockValidator class, which is responsible for validating calculated
summary blocks in a questionnaire schema. It inherits from the CalculationBlockValidator and adds additional validation
specific to calculated summary blocks.

Classes:
    CalculatedSummaryBlockValidator
"""

from app.validators.blocks.calculation_block_validator import CalculationBlockValidator


class CalculatedSummaryBlockValidator(CalculationBlockValidator):
    """Validator for calculated summary blocks. Inherits from CalculationBlockValidator and adds additional validation.

    Attributes:
        block (dict): The block to be validated.
        questionnaire_schema (QuestionnaireSchema): The questionnaire schema to validate against.

    Methods:
        validate
        validate_single_answer_is_for_repeating_answers
        validate_answer_id_set_before_calculated_summary_block
        validate_answer_id_for_calculated_summary_not_in_different_section
    """

    ANSWER_SET_AFTER_CALCULATED_SUMMARY = (
        "Answer ids for calculated summary must be set before calculated summary block"
    )
    ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY = (
        "Answer ids for calculated summary must be set in the same section as the calculated summary block"
    )
    CALCULATED_SUMMARY_WITH_NON_REPEATING_SINGLE_ANSWER = (
        "Calculated summaries cannot consist of a single answer unless it is a repeating answer"
    )

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.questionnaire_schema.get_calculation_block_ids(
            block=self.block,
            source_type="answers",
        )

    def validate(self):
        """Validate the calculated summary block by performing several checks on the answers to be calculated.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_single_answer_is_for_repeating_answers(answers)
        self.validate_answer_id_set_before_calculated_summary_block()
        self.validate_answer_id_for_calculated_summary_not_in_different_section()

        self.validate_answer_types(answers)

        return self.errors

    def validate_single_answer_is_for_repeating_answers(self, answers: list[dict]):
        """Validate that if there is only one answer in the answers_to_calculate list, it's for repeating answers.

        Args:
            answers: A list of answer dictionaries to be calculated in the calculated summary block.
        """
        if len(answers) == 1:
            single_answer_id = answers[0]["id"]
            # check if its dynamic
            if question_block := self.questionnaire_schema.get_block_by_answer_id(
                single_answer_id,
            ):
                if single_answer_id in self.questionnaire_schema.get_all_dynamic_answer_ids(
                    question_block["id"],
                ):
                    return
                # check if it's for a repeating question
                if question_block["type"] == "ListRepeatingQuestion":
                    return

            self.add_error(
                self.CALCULATED_SUMMARY_WITH_NON_REPEATING_SINGLE_ANSWER,
                block_id=self.block["id"],
                answer_id=single_answer_id,
            )

    def validate_answer_id_set_before_calculated_summary_block(self):
        """Validate that answer ids in the answers_to_calculate list are set before the calculated summary block."""
        for answer_id in self.answers_to_calculate:
            answer_id_block = self.questionnaire_schema.get_block_id_by_answer_id(
                answer_id,
            )
            if self.questionnaire_schema.block_ids.index(
                answer_id_block,
            ) > self.questionnaire_schema.block_ids.index(self.block["id"]):
                self.add_error(
                    self.ANSWER_SET_AFTER_CALCULATED_SUMMARY,
                    block=self.block,
                )

    def validate_answer_id_for_calculated_summary_not_in_different_section(self):
        """Validate that all answer ids in the answers_to_calculate list are in the same section as the calculated
        summary block.
        """
        answer_section_ids = {
            self.questionnaire_schema.answers_with_context[answer_id]["section"]
            for answer_id in self.answers_to_calculate
        }
        if len(answer_section_ids) > 1:
            self.add_error(
                self.ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY,
                block_id=self.block["id"],
                section_ids=answer_section_ids,
            )
