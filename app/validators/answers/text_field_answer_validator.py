"""This module provides a validator for text field answers in questionnaires."""

import re
from urllib.parse import urlparse

from app.validators.answers.answer_validator import AnswerValidator


class TextFieldAnswerValidator(AnswerValidator):
    """Validates a text field answer."""

    INVALID_SUGGESTION_URL = "Suggestions url is invalid"

    def validate(self):
        """Validates the text field answer."""
        super().validate()
        self.validate_suggestions_url()
        return self.errors

    def validate_suggestions_url(self):
        """Validates the suggestions URL."""
        if "suggestions_url" in self.answer and not self.is_suggestion_url_valid():
            self.add_error(self.INVALID_SUGGESTION_URL)

    def is_suggestion_url_valid(self):
        """Check if the suggestions URL is valid."""
        parsed_result = urlparse(self.answer["suggestions_url"])

        if parsed_result.scheme and parsed_result.netloc:
            return True
        return re.match(r"^[A-Za-z0-9_.\-/~]+$", parsed_result.path) is not None
