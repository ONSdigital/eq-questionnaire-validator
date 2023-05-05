from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.calculation_block_validator import CalculationBlockValidator
from app.validators.questionnaire_schema import (
    find_dictionary_duplicates,
    find_duplicates,
)


class GrandCalculatedSummaryBlockValidator(CalculationBlockValidator):
    CALCULATED_SUMMARIES_HAS_DUPLICATES = (
        "Duplicate calculated summaries in block's value sources"
    )
    CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS = "Cannot have two calculated summaries referencing exactly the same answers in a grand calculated summary"
    CALCULATED_SUMMARY_CONFIRMED_AFTER_GRAND_CALCULATED_SUMMARY = "All calculated summaries must be confirmed before grand calculated summary block"
    GRAND_CALCULATED_SUMMARY_HAS_INVALID_SOURCE = (
        "All value sources for grand calculated summary must be calculated summaries"
    )
    CALCULATED_SUMMARY_HAS_INVALID_ID = (
        "Invalid calculated summary id in block's answers_to_calculate"
    )

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate: list[str] = []
        # check calculated summary answers sets to verify no two calculated summaries are identical
        self.calculated_summary_answers: dict[str, tuple[str, ...]] = {}
        self.calculated_summaries_to_calculate = (
            self.questionnaire_schema.get_calculation_block_ids(
                self.block, "calculated_summary"
            )
        )

    def validate(self):
        super().validate()

        if self.validate_calculated_summary_ids_to_calculate():
            return self.errors

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_grand_calculated_summary_sources_are_calculated_summaries()
        self.validate_calculated_summary_confirmed_before_grand_calculated_summary_block()

        if calculated_summary_answer_duplicates := find_dictionary_duplicates(
            self.calculated_summary_answers
        ):
            self.add_error(
                self.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
                duplicate_answers=calculated_summary_answer_duplicates,
            )

        if calculated_summary_duplicates := find_duplicates(
            self.calculated_summaries_to_calculate
        ):
            self.add_error(
                self.CALCULATED_SUMMARIES_HAS_DUPLICATES,
                duplicates=calculated_summary_duplicates,
            )

        self.validate_answer_types(answers)

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
                calculated_summary_block, "answers"
            )
            self.answers_to_calculate.extend(answers)
            self.calculated_summary_answers[calculated_summary_id] = tuple(answers)

    def validate_calculated_summary_confirmed_before_grand_calculated_summary_block(
        self,
    ):
        for calculated_summary_id in self.calculated_summaries_to_calculate:
            if self.questionnaire_schema.block_ids.index(
                calculated_summary_id
            ) > self.questionnaire_schema.block_ids.index(self.block["id"]):
                self.add_error(
                    self.CALCULATED_SUMMARY_CONFIRMED_AFTER_GRAND_CALCULATED_SUMMARY,
                    block=self.block,
                )

    def validate_grand_calculated_summary_sources_are_calculated_summaries(self):
        for value_source in self.block["calculation"]["operation"]["+"]:
            if value_source["source"] != "calculated_summary":
                self.add_error(
                    self.GRAND_CALCULATED_SUMMARY_HAS_INVALID_SOURCE,
                    block_id=self.block["id"],
                    value_source=value_source,
                )
