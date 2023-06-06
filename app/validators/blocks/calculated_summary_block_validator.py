from app.validators.blocks.calculation_block_validator import CalculationBlockValidator


class CalculatedSummaryBlockValidator(CalculationBlockValidator):
    ANSWER_SET_AFTER_CALCULATED_SUMMARY = (
        "Answer ids for calculated summary must be set before calculated summary block"
    )
    ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY = "Answer ids for calculated summary must be set in the same section as the calculated summary block"

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.questionnaire_schema.get_calculation_block_ids(
            block=self.block, source_type="answers"
        )

    def validate(self):
        super().validate()

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_answer_id_set_before_calculated_summary_block()
        self.validate_answer_id_for_calculated_summary_not_in_different_section()

        self.validate_answer_types(answers)

        return self.errors

    def validate_answer_id_set_before_calculated_summary_block(self):
        for answer_id in self.answers_to_calculate:
            answer_id_block = self.questionnaire_schema.get_block_id_by_answer_id(
                answer_id
            )
            if self.questionnaire_schema.block_ids.index(
                answer_id_block
            ) > self.questionnaire_schema.block_ids.index(self.block["id"]):
                self.add_error(
                    self.ANSWER_SET_AFTER_CALCULATED_SUMMARY, block=self.block
                )

    def validate_answer_id_for_calculated_summary_not_in_different_section(self):
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
