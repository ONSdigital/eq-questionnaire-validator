from app.validators.answers import TextFieldAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_textfield_validator():
    filename = "schemas/valid/test_interstitial_instruction.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "id": "favourite-lunch",
        "label": "What is your favourite lunchtime food",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "this isn't a valid url",
    }
    validator = TextFieldAnswerValidator(answer, schema)

    validator.validate()

    assert [
        {"message": validator.INVALID_SUGGESTION_URL, "answer_id": "favourite-lunch"}
    ] == validator.errors


def test_textfield_validator_success():
    filename = "schemas/valid/test_interstitial_instruction.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "id": "favourite-lunch",
        "label": "What is your favourite lunchtime food",
        "mandatory": False,
        "type": "TextField",
        "suggestions_url": "http://www.google.com/somepath",
    }
    validator = TextFieldAnswerValidator(answer, schema)

    validator.validate()

    assert not validator.errors
