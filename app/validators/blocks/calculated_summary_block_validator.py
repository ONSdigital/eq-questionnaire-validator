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

    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.block["calculation"]["answers_to_calculate"]

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

        duplicates = find_duplicates(self.answers_to_calculate)

        if duplicates:
            self.add_error(self.ANSWERS_HAS_DUPLICATES, duplicate_answers=duplicates)

        if not all(answer["type"] == answers[0]["type"] for answer in answers):
            self.add_error(self.ANSWERS_MUST_HAVE_SAME_TYPE)
            return self.errors

        if answers[0]["type"] == "Unit":
            if not all(answer["unit"] == answers[0]["unit"] for answer in answers):
                self.add_error(self.ANSWERS_MUST_HAVE_SAME_UNIT)
        elif answers[0]["type"] == "Currency":
            if not all(
                answer["currency"] == answers[0]["currency"] for answer in answers
            ):
                self.add_error(self.ANSWERS_MUST_HAVE_SAME_CURRENCY)
        return self.errors
