from app.validators.blocks.calculation_block_validator import CalculationBlockValidator
from app.validators.questionnaire_schema import find_dictionary_duplicates


class GrandCalculatedSummaryBlockValidator(CalculationBlockValidator):
    CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS = "Cannot have multiple calculated summaries referencing exactly the same answers in a grand calculated summary"
    CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY = "Cannot have a grand calculated summary before a calculated summary that it depends on"
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

        self.validate_calculated_summary_is_before_grand_calculated_summary_block()

        if calculated_summary_answer_duplicates := find_dictionary_duplicates(
            self.calculated_summary_answers
        ):
            self.add_error(
                self.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
                duplicate_answers=calculated_summary_answer_duplicates,
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
