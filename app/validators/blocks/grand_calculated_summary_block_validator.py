"""This module contains the GrandCalculatedSummaryBlockValidator class, which is responsible for validating grand
calculated summary blocks in a questionnaire schema.

Classes:
    GrandCalculatedSummaryBlockValidator
"""

from typing import Mapping

from app.validators.blocks.calculation_block_validator import CalculationBlockValidator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    find_dictionary_duplicates,
)


class GrandCalculatedSummaryBlockValidator(CalculationBlockValidator):
    """Validator for grand calculated summary blocks. Inherits from CalculationBlockValidator and adds additional
     validation.

    Attributes:
        block (dict): The block to be validated.
        questionnaire_schema (QuestionnaireSchema): The questionnaire schema to validate against.

    Methods:
        validate
        validate_calculated_summary_ids_to_calculate
        validate_calculated_summary_is_before_grand_calculated_summary_block
        validate_calculated_summaries
        _validate_static_calculated_summary_in_repeating_grand_calculated_summary
        _validate_repeating_calculated_summary_in_grand_calculated_summary
    """
    CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS = (
        "Cannot have multiple calculated summaries referencing exactly the same answers in a grand calculated summary"
    )
    CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY = (
        "Cannot have a grand calculated summary before a calculated summary that it depends on"
    )
    CALCULATED_SUMMARY_HAS_INVALID_ID = "Invalid calculated summary id in block's answers_to_calculate"
    REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT = (
        "Cannot have a non-repeating grand calculated summary reference a repeating calculated summary"
    )
    CALCULATED_SUMMARY_IN_DIFFERENT_REPEATING_SECTION = (
        "Cannot have a repeating grand calculated summary reference"
        " a repeating calculated summary in a different repeating section"
    )
    CALCULATED_SUMMARY_WITH_REPEATING_ANSWERS_FOR_SAME_LIST = (
        "Cannot have a repeating grand calculated summary reference a static calculated summary"
        " that has repeating answers for the same list"
    )

    def __init__(self, block: Mapping, questionnaire_schema: QuestionnaireSchema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate: list[str] = []
        # check calculated summary answers sets to verify no two calculated summaries are identical
        self.calculated_summary_answers: dict[str, tuple[str, ...]] = {}
        self.calculated_summaries_to_calculate = self.questionnaire_schema.get_calculation_block_ids(
            block=self.block,
            source_type="calculated_summary",
        )

    def validate(self):
        """Validates the grand calculated summary block by performing several checks on the calculated summaries to be
         calculated.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()

        if self.validate_calculated_summary_ids_to_calculate():
            return self.errors

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_calculated_summary_is_before_grand_calculated_summary_block()

        if calculated_summary_answer_duplicates := find_dictionary_duplicates(
            self.calculated_summary_answers,
        ):
            self.add_error(
                self.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
                duplicate_answers=calculated_summary_answer_duplicates,
            )

        self.validate_answer_types(answers)
        self.validate_calculated_summaries()

        return self.errors

    def validate_calculated_summary_ids_to_calculate(self):
        """Validates that all calculated summary ids in the calculated_summaries_to_calculate list are valid.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            calculated_summary_block = self.questionnaire_schema.get_block(
                calculated_summary_id,
            )
            if not calculated_summary_block or not calculated_summary_block.get(
                "calculation",
            ):
                self.add_error(self.CALCULATED_SUMMARY_HAS_INVALID_ID)
                return self.errors
            answers = self.questionnaire_schema.get_calculation_block_ids(
                block=calculated_summary_block,
                source_type="answers",
            )
            self.answers_to_calculate.extend(answers)
            self.calculated_summary_answers[calculated_summary_id] = tuple(answers)

    def validate_calculated_summary_is_before_grand_calculated_summary_block(
        self,
    ):
        """Validates that all calculated summary blocks are before the grand calculated summary block in the
        questionnaire schema.
        """
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            if self.questionnaire_schema.block_ids.index(
                calculated_summary_id,
            ) > self.questionnaire_schema.block_ids.index(self.block["id"]):
                self.add_error(
                    self.CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY,
                    block_id=self.block["id"],
                    calculated_summary_id=calculated_summary_id,
                )

    def validate_calculated_summaries(self):
        """Validates that any grand calculated summary is referencing a repeating calculated summary and repeating
        grand calculated summary is referencing a static calculated summary.
        """
        if grand_calculated_summary_section := self.questionnaire_schema.get_parent_section_for_block(self.block["id"]):
            is_grand_calculated_summary_repeating = self.questionnaire_schema.is_repeating_section(
                grand_calculated_summary_section["id"],
            )
            for calculated_summary_id in self.calculated_summaries_to_calculate:
                if self.questionnaire_schema.is_block_in_repeating_section(
                    calculated_summary_id,
                ):
                    self._validate_repeating_calculated_summary_in_grand_calculated_summary(
                        calculated_summary_id=calculated_summary_id,
                        is_grand_calculated_summary_repeating=is_grand_calculated_summary_repeating,
                        grand_calculated_summary_section_id=grand_calculated_summary_section["id"],
                    )
                elif is_grand_calculated_summary_repeating:
                    list_name = grand_calculated_summary_section["repeat"]["for_list"]
                    self._validate_static_calculated_summary_in_repeating_grand_calculated_summary(
                        list_name=list_name,
                        calculated_summary_id=calculated_summary_id,
                    )

    def _validate_static_calculated_summary_in_repeating_grand_calculated_summary(
        self,
        *,
        list_name: str,
        calculated_summary_id: str,
    ):
        """Validates that the grand calculated summary is correctly referencing a static calculated summary.
        If the grand calculated summary is repeating, and references a static calculated summary with repeating answers,
        this is only valid if the repeating answers are for a different list to the grand calculated summary.

        Args:
            list_name: The name of the list that the grand calculated summary is repeating for.
            calculated_summary_id: The id of the calculated summary block being validated.
        """
        for answer_id in self.calculated_summary_answers[calculated_summary_id]:
            if (
                answer_list := self.questionnaire_schema.get_list_name_for_answer_id(
                    answer_id,
                )
            ) and answer_list == list_name:
                self.add_error(
                    self.CALCULATED_SUMMARY_WITH_REPEATING_ANSWERS_FOR_SAME_LIST,
                    block_id=self.block["id"],
                    calculated_summary_id=calculated_summary_id,
                    list_name=list_name,
                )

    def _validate_repeating_calculated_summary_in_grand_calculated_summary(
        self,
        *,
        calculated_summary_id: str,
        is_grand_calculated_summary_repeating: bool,
        grand_calculated_summary_section_id: str,
    ):
        """Validates that the grand calculated summary is correctly referencing a repeating calculated summary.
        If the grand calculated summary references a repeating calculated summary, this is only valid if the grand
        calculated summary is also repeating, or it is in the same repeating section as the repeating calculated
        summary it references.

        Args:
            calculated_summary_id: The id of the calculated summary block being validated.
            is_grand_calculated_summary_repeating: Whether the grand calculated summary block is in a repeating section.
            grand_calculated_summary_section_id: The id of the section the grand calculated summary block is in.
        """
        if not is_grand_calculated_summary_repeating:
            self.add_error(
                self.REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT,
                block_id=self.block["id"],
                calculated_summary_id=calculated_summary_id,
            )
        elif grand_calculated_summary_section_id != self.questionnaire_schema.get_section_id_for_block_id(
            calculated_summary_id,
        ):
            self.add_error(
                self.CALCULATED_SUMMARY_IN_DIFFERENT_REPEATING_SECTION,
                block_id=self.block["id"],
                calculated_summary_id=calculated_summary_id,
            )
