from app import error_messages
from app.validators.blocks.block_validator import BlockValidator


class CalculatedSummaryBlockValidator(BlockValidator):
    def __init__(self, block, questionnaire_schema):
        super().__init__(block, questionnaire_schema)
        self.answers_to_calculate = self.block["calculation"]["answers_to_calculate"]

    def validate(self):
        super(CalculatedSummaryBlockValidator, self).validate()

        try:
            answers = [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"]
                for answer_id in self.answers_to_calculate
            ]
        except KeyError as e:
            self.add_error(
                error_messages.ANSWERS_TO_CALCULATE_HAS_INVALID_ID,
                answer_id=str(e).strip("'"),
            )
            return

        duplicates = {
            answer_id
            for answer_id in self.answers_to_calculate
            if self.answers_to_calculate.count(answer_id) > 1
        }
        if duplicates:
            self.add_error(
                error_messages.ANSWERS_TO_CALCULATE_HAS_DUPLICATES,
                duplicate_answers=duplicates,
            )
            return

        if not all(answer["type"] == answers[0]["type"] for answer in answers):
            self.add_error(error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_TYPE)
            return

        if answers[0]["type"] == "Unit":
            if not all(answer["unit"] == answers[0]["unit"] for answer in answers):
                self.add_error(error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_UNIT)
                return

        if answers[0]["type"] == "Currency":
            if not all(
                answer["currency"] == answers[0]["currency"] for answer in answers
            ):
                self.add_error(
                    error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_CURRENCY
                )
