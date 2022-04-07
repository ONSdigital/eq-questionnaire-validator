import pytest

from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.value_source_validator import ValueSourceValidator


@pytest.mark.parametrize(
    "value_source",
    [
        {"source": "list", "identifier": "people"},
        {"source": "answers", "identifier": "answer-2"},
        {"source": "metadata", "identifier": "submitted_at"},
        {"source": "response_metadata", "identifier": "submitted_at"},
        {"source": "calculated_summary", "identifier": "total-turnover"},
    ],
)
def test_invalid_source_reference(value_source):
    questionnaire_schema = QuestionnaireSchema(
        {"metadata": [{"name": "metatata-1", "type": "string"}]}
    )
    questionnaire_schema.list_names = ["list-1"]
    questionnaire_schema.calculated_summary_block_ids = ["block-1"]
    questionnaire_schema.answers_with_context = {
        "answer-1": {"answer": {"id": "answer-1", "type": "TextField"}}
    }

    validator = ValueSourceValidator(
        value_source, "some.json.path", questionnaire_schema
    )
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.SOURCE_REFERENCE_INVALID.format(
        value_source["source"]
    )
    assert error["identifier"] == value_source["identifier"]
    assert error["json_path"] == "some.json.path"


def test_invalid_reference():
    value_source = {"source": "answers", "identifier": "answer-2"}

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "answer-1": {"answer": {"id": "answer-1", "type": "TextField"}}
    }
    validator = ValueSourceValidator(value_source, "", questionnaire_schema)
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID
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
