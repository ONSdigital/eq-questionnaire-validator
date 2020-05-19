from app import error_messages
from app.validators.answers import TextFieldAnswerValidator


def test_textfield_validator():
    answer = {
        "id": "answer-1",
        "label": "Answer 1",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "this isn't a valid url",
    }
    validator = TextFieldAnswerValidator(answer)

    validator.validate()

    assert [
        {"message": error_messages.INVALID_SUGGESTION_URL, "answer_id": "answer-1"}
    ] == validator.errors


def test_textfield_validator_success():
    answer = {
        "id": "answer-1",
        "label": "Answer 1",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "http://www.google.com/somepath",
    }
    validator = TextFieldAnswerValidator(answer)

    validator.validate()

    assert [] == validator.errors
