from app.validators.answers import TextFieldAnswerValidator
from tests.conftest import get_mock_schema_with_data_version


def test_textfield_validator():
    answer = {
        "id": "answer-1",
        "label": "Answer 1",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "this isn't a valid url",
    }
    validator = TextFieldAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )

    validator.validate()

    assert [
        {"message": validator.INVALID_SUGGESTION_URL, "answer_id": "answer-1"}
    ] == validator.errors


def test_textfield_validator_success():
    answer = {
        "id": "answer-1",
        "label": "Answer 1",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "http://www.google.com/somepath",
    }
    validator = TextFieldAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )

    validator.validate()

    assert not validator.errors
