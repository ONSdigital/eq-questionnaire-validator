"""This module contains the CalculationBlockValidator class, which validates that all answers in a calculation block
are of the same type, and if they are of type "Unit" or "Currency", that they have the same unit or currency
respectively.

Classes:
    CalculationBlockValidator

Functions:
    is_value_for_key_unique

"""

from app.validators.blocks.block_validator import BlockValidator


def is_value_for_key_unique(dictionaries: list[dict], key: str) -> bool:
    """Checks if the value for a given key is the same across all dictionaries in the list.

    Args:
        dictionaries: A list of dictionaries to check.
        key: The key for which to check the uniqueness of the value.

    Returns:
        bool: True if the value for the given key is the same across all dictionaries, False otherwise.
    """
    value_error_message = "check for unique values can't be called with an empty list"
    if not dictionaries:
        raise ValueError(value_error_message)
    first_value = dictionaries[0].get(key)
    return all(dictionary.get(key) == first_value for dictionary in dictionaries)


class CalculationBlockValidator(BlockValidator):
    """Calculation Block Validator.
    Both Calculated summaries and grand calculated summaries require all answers
    to be of the same type so this validation can be reused.

    Methods:
        get_answers
        validate_answer_types
    """

    ANSWERS_MUST_HAVE_SAME_TYPE = "All answers in block's answers_to_calculate must be of the same type"
    ANSWERS_MUST_HAVE_SAME_CURRENCY = "All answers in block's answers_to_calculate must be of the same currency"
    ANSWERS_MUST_HAVE_SAME_UNIT = "All answers in block's answers_to_calculate must be of the same unit"
    ANSWERS_HAS_INVALID_ID = "Invalid answer id in block's answers_to_calculate"

    def get_answers(self, answers_to_calculate) -> list[dict] | None:
        """Gets the answers for the given answer ids in the answers_to_calculate list. If any of the answer ids are
        invalid, an error is added to the errors list.

        Args:
            answers_to_calculate (list): A list of answer ids to be calculated in the calculation block.

        Returns:
            A list of answers only if the answer with relevant answer_id is found for all answers in
            answers_with_context object.
        """
        try:
            return [
                self.questionnaire_schema.answers_with_context[answer_id]["answer"]
                for answer_id in answers_to_calculate
            ]
        except KeyError as e:
            self.add_error(self.ANSWERS_HAS_INVALID_ID, answer_id=str(e).strip("'"))
        return None

    def validate_answer_types(self, answers: list[dict]) -> None:
        """Validates that all answers in the answers list are of the same type and that they have the same unit
        or currency respectively.

        Args:
            answers: A list of answers to validate.
        """
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
