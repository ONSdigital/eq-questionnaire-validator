import re
from urllib.parse import urlparse

from app import error_messages
from app.validators.answers.answer_validator import AnswerValidator


class TextFieldAnswerValidator(AnswerValidator):
    def validate(self):
        super(TextFieldAnswerValidator, self).validate()

        if (
            self.answer["type"] == "TextField"
            and "suggestions_url" in self.answer
            and not self.is_suggestion_url_valid()
        ):
            self.add_error(error_messages.INVALID_SUGGESTION_URL)

    def is_suggestion_url_valid(self):
        parsed_result = urlparse(self.answer["suggestions_url"])

        if parsed_result.scheme and parsed_result.netloc:
            return True
        return re.match(r"^[A-Za-z0-9_.\-/~]+$", parsed_result.path) is not None
