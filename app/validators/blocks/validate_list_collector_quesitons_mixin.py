"""This module contains the ValidateListCollectorQuestionsMixin class, which provides validation methods for list
collector questions.

Classes:
    ValidateListCollectorQuestionsMixin

Functions:
    _options_contain_action_type
"""

from app.validators.validator import Validator


def _options_contain_action_type(options, expected_action):
    """Checks if any option in the provided list of options contains an action of the expected type.

    Args:
        options (list): A list of option dictionaries to check.
        expected_action (str): The expected action type to look for in the options.

    Returns:
        bool: True if any option contains an action of the expected type, False otherwise.
    """
    return any(option["action"]["type"] == expected_action for option in options if "action" in option)


class ValidateListCollectorQuestionsMixin(Validator):
    """Mixin class that provides validation methods for list collector questions.

    Methods:
        validate_collector_questions
        validate_same_name_answer_ids
    """

    MISSING_SAME_NAME_ANSWER_ID = "Invalid id in same_name_answer_ids"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_collector_questions(
        self,
        collector_questions,
        missing_radio_error,
        expected_action,
        missing_action_error,
    ):
        """Validates that all collector questions have a Radio answer type and contain the expected action type
        in their options.

        Args:
            collector_questions (list): A list of collector question dictionaries to validate.
            missing_radio_error (str): The error message to add if a question does not have a Radio answer type.
            expected_action (str): The expected action type to look for in the options
            missing_action_error (str): The error message to add if a question's options do not contain the expected
            action type.
        """
        for collector_question in collector_questions:
            for collector_answer in collector_question["answers"]:
                if collector_answer["type"] != "Radio":
                    self.add_error(missing_radio_error)

                if not _options_contain_action_type(
                    collector_answer["options"],
                    expected_action,
                ):
                    self.add_error(missing_action_error)

    def validate_same_name_answer_ids(self, answer_ids):
        """Validates that all answer ids in the same_name_answer_ids list are present in the provided answer_ids list.

        Args:
            answer_ids (list): A list of answer ids to validate against the same_name_answer_ids list.
        """
        same_name_item_answer_ids = self.schema_element.get("same_name_answer_ids", [])

        for same_name_answer_id in same_name_item_answer_ids:
            if same_name_answer_id not in answer_ids:
                self.add_error(
                    self.MISSING_SAME_NAME_ANSWER_ID,
                    answer_id=same_name_answer_id,
                )
