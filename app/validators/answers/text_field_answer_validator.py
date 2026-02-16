"""This module contains the TextFieldAnswerValidator class, which is responsible for validating answers of type
"text_field".

Classes:
    TextFieldAnswerValidator
"""

import re
from urllib.parse import urlparse

from app.validators.answers.answer_validator import AnswerValidator


class TextFieldAnswerValidator(AnswerValidator):
    """Validates answers of type "text_field" in a questionnaire schema.

    Methods:
        validate
        validate_suggestions_url
        is_suggestion_url_valid
    """

    INVALID_SUGGESTION_URL = "Suggestions url is invalid"

    def validate(self):
        """Validates the text field answer by first invoking the parent validate method and then checking if the
        suggestions.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()
        self.validate_suggestions_url()
        return self.errors

    def validate_suggestions_url(self):
        """Validates the suggestions_url property of the answer if it is present and by calling the
        is_suggestion_url_valid method to check if it is a valid.
        """
        if "suggestions_url" in self.answer and not self.is_suggestion_url_valid():
            self.add_error(self.INVALID_SUGGESTION_URL)

    def is_suggestion_url_valid(self):
        """Checks if the suggestions_url is a valid URL by parsing it and ensuring it has a scheme and netloc, or if it
        is a valid relative URL by matching it against a regular expression.

        Returns:
            bool: True if the suggestions_url is a valid URL or a valid relative URL, False otherwise.
        """
        parsed_result = urlparse(self.answer["suggestions_url"])

        if parsed_result.scheme and parsed_result.netloc:
            return True
        return re.match(r"^[A-Za-z0-9_.\-/~]+$", parsed_result.path) is not None
