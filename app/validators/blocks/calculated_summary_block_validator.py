from app.validators.blocks.block_validator import BlockValidator
from app.validators.questionnaire_schema import find_duplicates


class CalculatedSummaryBlockValidator(BlockValidator):
    ANSWERS_MUST_HAVE_SAME_TYPE = (
        "All answers in block's answers_to_calculate must be of the same type"
    )
    ANSWERS_MUST_HAVE_SAME_CURRENCY = (
        "All answers in block's answers_to_calculate must be of the same currency"
    )
    ANSWERS_MUST_HAVE_SAME_UNIT = (
        "All answers in block's answers_to_calculate must be of the same unit"
    )
    ANSWERS_HAS_INVALID_ID = "Invalid answer id in block's answers_to_calculate"
    ANSWERS_HAS_DUPLICATES = "Duplicate answers in block's answers_to_calculate"
    ANSWER_SET_AFTER_CALCULATED_SUMMARY = (
        "Answer ids for calculated summary must be set before calculated summary block"
    )
    ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY = "Answer ids for calculated summary must be set in the same section as the calculated summary block"

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.questionnaire_schema.get_calculated_answer_ids(
            self.block
        )

    def validate(self):
        super().validate()

        try:
            answers = [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"]
                for answer_id in self.answers_to_calculate
            ]
        except KeyError as e:
            self.add_error(self.ANSWERS_HAS_INVALID_ID, answer_id=str(e).strip("'"))
            return self.errors

        self.validate_answer_id_set_before_calculated_summary_block()

        self.validate_answer_id_for_calculated_summary_not_in_different_section()

        if duplicates := find_duplicates(self.answers_to_calculate):
            self.add_error(self.ANSWERS_HAS_DUPLICATES, duplicate_answers=duplicates)

        if any(answer["type"] != answers[0]["type"] for answer in answers):
            self.add_error(self.ANSWERS_MUST_HAVE_SAME_TYPE)
            return self.errors

        if answers[0]["type"] == "Unit":
            if any(answer["unit"] != answers[0]["unit"] for answer in answers):
                self.add_error(self.ANSWERS_MUST_HAVE_SAME_UNIT)
        elif answers[0]["type"] == "Currency":
            if any(answer["currency"] != answers[0]["currency"] for answer in answers):
                self.add_error(self.ANSWERS_MUST_HAVE_SAME_CURRENCY)
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
