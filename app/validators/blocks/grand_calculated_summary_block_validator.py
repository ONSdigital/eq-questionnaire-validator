from app.validators.blocks.calculation_block_validator import CalculationBlockValidator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    find_dictionary_duplicates,
)


class GrandCalculatedSummaryBlockValidator(CalculationBlockValidator):
    CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS = "Cannot have multiple calculated summaries referencing exactly the same answers in a grand calculated summary"
    CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY = "Cannot have a grand calculated summary before a calculated summary that it depends on"
    CALCULATED_SUMMARY_HAS_INVALID_ID = (
        "Invalid calculated summary id in block's answers_to_calculate"
    )
    REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT = "Cannot have a non-repeating grand calculated summary reference a repeating calculated summary"
    CALCULATED_SUMMARY_IN_DIFFERENT_REPEATING_SECTION = (
        "Cannot have a repeating grand calculated summary reference"
        " a repeating calculated summary in a different repeating section"
    )

    def __init__(self, block, questionnaire_schema: QuestionnaireSchema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate: list[str] = []
        # check calculated summary answers sets to verify no two calculated summaries are identical
        self.calculated_summary_answers: dict[str, tuple[str, ...]] = {}
        self.calculated_summaries_to_calculate = (
            self.questionnaire_schema.get_calculation_block_ids(
                block=self.block, source_type="calculated_summary"
            )
        )

    def validate(self):
        super().validate()

        if self.validate_calculated_summary_ids_to_calculate():
            return self.errors

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_calculated_summary_is_before_grand_calculated_summary_block()

        if calculated_summary_answer_duplicates := find_dictionary_duplicates(
            self.calculated_summary_answers
        ):
            self.add_error(
                self.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
                duplicate_answers=calculated_summary_answer_duplicates,
            )

        self.validate_answer_types(answers)
        self.validate_repeating_calculated_summaries()

        return self.errors

    def validate_calculated_summary_ids_to_calculate(self):
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            calculated_summary_block = self.questionnaire_schema.get_block(
                calculated_summary_id
            )
            if not calculated_summary_block or not calculated_summary_block.get(
                "calculation"
            ):
                self.add_error(self.CALCULATED_SUMMARY_HAS_INVALID_ID)
                return self.errors
            answers = self.questionnaire_schema.get_calculation_block_ids(
                block=calculated_summary_block, source_type="answers"
            )
            self.answers_to_calculate.extend(answers)
            self.calculated_summary_answers[calculated_summary_id] = tuple(answers)

    def validate_calculated_summary_is_before_grand_calculated_summary_block(
        self,
    ):
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            if self.questionnaire_schema.block_ids.index(
                calculated_summary_id
            ) > self.questionnaire_schema.block_ids.index(self.block["id"]):
                self.add_error(
                    self.CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY,
                    block_id=self.block["id"],
                    calculated_summary_id=calculated_summary_id,
                )

    def validate_repeating_calculated_summaries(self):
        """
        If the grand calculated summary references a repeating calculated summary, this is only valid if:
        1) the grand calculated summary is also repeating
        2) it is in the same repeating section as the repeating calculated summary it references
        """
        gcs_section_id = self.questionnaire_schema.get_section_id_for_block_id(
            self.block["id"]
        )
        is_gcs_repeating = self.questionnaire_schema.is_repeating_section(
            gcs_section_id
        )
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            if not self.questionnaire_schema.is_block_in_repeating_section(
                calculated_summary_id
            ):
                # validation below only required for repeating calculated summaries
                continue

            if not is_gcs_repeating:
                self.add_error(
                    self.REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT,
                    block_id=self.block["id"],
                    calculated_summary_id=calculated_summary_id,
                )
            elif (
                gcs_section_id
                != self.questionnaire_schema.get_section_id_for_block_id(
                    calculated_summary_id
                )
            ):
                self.add_error(
                    self.CALCULATED_SUMMARY_IN_DIFFERENT_REPEATING_SECTION,
                    block_id=self.block["id"],
                    calculated_summary_id=calculated_summary_id,
                )
