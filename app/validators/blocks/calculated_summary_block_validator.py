from app.validators.blocks.calculation_block_validator import CalculationBlockValidator


class CalculatedSummaryBlockValidator(CalculationBlockValidator):
    ANSWER_SET_AFTER_CALCULATED_SUMMARY = (
        "Answer ids for calculated summary must be set before calculated summary block"
    )
    ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY = "Answer ids for calculated summary must be set in the same section as the calculated summary block"
    CALCULATED_SUMMARY_WITH_NON_DYNAMIC_SINGLE_ANSWER = "Calculated summaries cannot consist of a single answer unless it is a dynamic answer"

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.questionnaire_schema.get_calculation_block_ids(
            block=self.block, source_type="answers"
        )

    def validate(self):
        super().validate()

        if (answers := self.get_answers(self.answers_to_calculate)) is None:
            return self.errors

        self.validate_single_answer_is_for_repeating_answers(answers)
        self.validate_answer_id_set_before_calculated_summary_block()
        self.validate_answer_id_for_calculated_summary_not_in_different_section()

        self.validate_answer_types(answers)

        return self.errors

    def validate_single_answer_is_for_repeating_answers(self, answers: list[dict]):
        """Validate that if there is only one answer in the answers_to_calculate list, it's for repeating answers"""
        if len(answers) == 1:
            single_answer_id = answers[0]["id"]
            # check if its dynamic
            if (
                single_answer_id
                in self.questionnaire_schema.get_all_dynamic_answer_ids(
                    self.questionnaire_schema.get_block_id_by_answer_id(
                        single_answer_id
                    )
                )
            ):
                return
            # check if it's for a repeating question
            question_block = self.questionnaire_schema.get_block_by_answer_id(
                single_answer_id
            )
            if question_block["type"] == "ListRepeatingQuestion":
                return

            self.add_error(
                self.CALCULATED_SUMMARY_WITH_NON_DYNAMIC_SINGLE_ANSWER,
                block_id=self.block["id"],
                answer_id=single_answer_id,
            )

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
