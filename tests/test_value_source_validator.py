from app.validators.value_source_validator import ValueSourceValidator
from app.validators.questionnaire_schema import QuestionnaireSchema


def test_invalid_reference():
    value_source = {"source": "answers", "identifier": "answer-2"}

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "answer-1": {"answer": {"id": "answer-1", "type": "TextField"}}
    }
    validator = ValueSourceValidator(value_source, "", questionnaire_schema)
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.ANSWER_REFERENCE_INVALID
    assert error["identifier"] == "answer-2"


def test_invalid_composite_answer_in_selector():
    value_source = {
        "identifier": "name-answer",
        "source": "answers",
        "selector": "line1",
    }

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "name-answer": {
            "answer": {"id": "name-answer", "type": "TextField"},
            "block": "name",
        }
    }
    validator = ValueSourceValidator(value_source, "", questionnaire_schema)
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.COMPOSITE_ANSWER_INVALID
    assert error["identifier"] == "name-answer"


def test_invalid_composite_answer_field_in_selector():
    value_source = {
        "identifier": "address-answer",
        "source": "answers",
        "selector": "invalid-field",
    }

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "address-answer": {
            "answer": {"id": "address-answer", "type": "Address"},
            "block": "name",
        }
    }
    validator = ValueSourceValidator(value_source, "", questionnaire_schema)
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.COMPOSITE_ANSWER_FIELD_INVALID
    assert error["identifier"] == "address-answer"


def test_invalid_placeholder_list_reference():
    value_source = {"identifier": "people", "source": "list", "selector": "count"}

    questionnaire_schema = QuestionnaireSchema({})
    validator = ValueSourceValidator(value_source, "", questionnaire_schema)
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.LIST_REFERENCE_INVALID
    assert error["identifier"] == "people"
