from app.validation import error_messages
from app.validation.blocks.block_validator import BlockValidator


class CalculatedSummaryBlockValidator(BlockValidator):
    def __init__(self, block, questionnaire_schema):
        self.questionnaire_schema = questionnaire_schema
        super(CalculatedSummaryBlockValidator, self).__init__(block)

    def validate(self):
        answers_to_calculate = self.block["calculation"]["answers_to_calculate"]

        try:
            answer_types = [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"][
                    "type"
                ]
                for answer_id in answers_to_calculate
            ]
        except KeyError as e:
            self.add_error(
                error_messages.ANSWERS_TO_CALCULATE_HAS_INVALID_ID,
                answer_id=str(e).strip("'"),
            )
            return

        duplicates = {
            answer
            for answer in answers_to_calculate
            if answers_to_calculate.count(answer) > 1
        }
        if duplicates:
            self.add_error(
                error_messages.ANSWERS_TO_CALCULATE_HAS_DUPLICATES,
                duplicate_answers=duplicates,
            )
            return

        if not all(answer_type == answer_types[0] for answer_type in answer_types):
            self.add_error(error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_TYPE)
            return

        if answer_types[0] == "Unit":
            unit_types = [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"][
                    "unit"
                ]
                for answer_id in answers_to_calculate
            ]
            if not all(unit_type == unit_types[0] for unit_type in unit_types):
                self.add_error(error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_UNIT)
                return

        if answer_types[0] == "Currency":
            currency_types = [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"][
                    "currency"
                ]
                for answer_id in answers_to_calculate
            ]
            if not all(
                currency_type == currency_types[0] for currency_type in currency_types
            ):
                self.add_error(
                    error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_CURRENCY
                )
