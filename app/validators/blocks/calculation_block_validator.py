"""CalculationBlockValidator validates calculation blocks in a questionnaire schema."""

from app.validators.blocks.block_validator import BlockValidator


def is_value_for_key_unique(dictionaries: list[dict], key: str) -> bool:
    """Checks if every dictionary provided has the same value for the given key."""
    value_error_message = "check for unique values can't be called with an empty list"
    if not dictionaries:
        raise ValueError(value_error_message)
    first_value = dictionaries[0].get(key)
    return all(dictionary.get(key) == first_value for dictionary in dictionaries)


class CalculationBlockValidator(BlockValidator):
    """CalculationBlockValidator validates calculation blocks in a questionnaire schema.

    Both Calculated summaries and grand calculated summaries require all answers to be of the same type
    so this validation can be reused.
    """

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

    def get_answers(self, answers_to_calculate) -> list[dict] | None:
        """Returns the answers only if all of them have valid ids."""
        try:
            return [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"]
                for answer_id in answers_to_calculate
            ]
        except KeyError as e:
            self.add_error(self.ANSWERS_HAS_INVALID_ID, answer_id=str(e).strip("'"))

    def validate_answer_types(self, answers: list[dict]) -> None:
        """Validates that all answers have the same type."""
        answer_type = answers[0]["type"]
        if not is_value_for_key_unique(answers, "type"):
            self.add_error(self.ANSWERS_MUST_HAVE_SAME_TYPE)
            return

        if answer_type == "Unit" and not is_value_for_key_unique(answers, "unit"):
            self.add_error(self.ANSWERS_MUST_HAVE_SAME_UNIT)
        elif answer_type == "Currency" and not is_value_for_key_unique(
            answers,
            "currency",
        ):
            self.add_error(self.ANSWERS_MUST_HAVE_SAME_CURRENCY)
