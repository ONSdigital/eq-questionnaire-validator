import re
from urllib.parse import urlparse

from app.validators.answers.answer_validator import AnswerValidator


class TextFieldAnswerValidator(AnswerValidator):
    INVALID_SUGGESTION_URL = "Suggestions url is invalid"

    def validate(self):
        super().validate()
        self.validate_suggestions_url()
        return self.errors

    def validate_suggestions_url(self):
        if "suggestions_url" in self.answer and not self.is_suggestion_url_valid():
            self.add_error(self.INVALID_SUGGESTION_URL)

    def is_suggestion_url_valid(self):
        if isinstance(self.answer["suggestions_url"], str):
            return re.match(r"[A-Za-z0-9_'{}.:\/-]", self.answer["suggestions_url"]) is not None
        if isinstance(self.answer["suggestions_url"], dict):
            return re.match(r"[A-Za-z0-9_'{}.:\/-]", self.answer["suggestions_url"]["text"]) is not None

