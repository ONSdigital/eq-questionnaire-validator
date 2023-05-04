import pytest

from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.value_source_validator import ValueSourceValidator
from tests.conftest import get_mock_schema_with_data_version


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
    questionnaire_schema.block_ids = ["block-2"]
    questionnaire_schema.section_ids = ["section-1"]
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


def test_invalid_progress_source_reference():
    invalid_value_source = {
        "source": "progress",
        "selector": "block",
        "identifier": "people",
    }
    questionnaire_schema = QuestionnaireSchema(
        {"metadata": [{"name": "metatata-1", "type": "string"}]}
    )
    questionnaire_schema.block_ids = ["blocktest"]
    questionnaire_schema.block_ids_without_sub_blocks = ["blocktest"]
    questionnaire_schema.section_ids = ["sectiontest"]

    questionnaire_schema.answers_with_context = {
        "answer-1": {"answer": {"id": "answer-1", "type": "TextField"}}
    }

    mock_block = {
        "id": "blocktest",
        "skip_conditions": {"when": {"==": [invalid_value_source, 1]}},
    }
    mock_section = {"id": "sectiontest", "blocks": [mock_block]}

    validator = ValueSourceValidator(
        invalid_value_source,
        "some.json.path",
        questionnaire_schema,
        parent_section=mock_section,
        parent_block=mock_block,
    )
    validator.validate()

    error = validator.errors[0]
    assert error["message"] == ValueSourceValidator.SOURCE_REFERENCE_INVALID.format(
        invalid_value_source["source"]
    )
    assert error["identifier"] == invalid_value_source["identifier"]
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


def test_answer_source_refrences_value_source():
    value_sources = [
        {
            "identifier": "set-minimum",
            "source": "answers",
        },
        {
            "identifier": "set-maximum",
            "source": "answers",
        },
    ]

    answer = {
        "id": "min-max-range",
        "mandatory": False,
        "minimum": {"value": {"identifier": "set-minimum", "source": "answers"}},
        "maximum": {"value": {"identifier": "set-maximum", "source": "answers"}},
        "type": "Number",
    }

    answers = {"answers": [answer]}
    questionnaire_schema = QuestionnaireSchema(answers)

    questionnaire_schema.answers_with_context = {
        "set-maximum": {"answer": {"id": "set-maximum", "type": "Number"}},
        "set-minimum": {"answer": {"id": "set-minimum", "type": "Number"}},
        "min-max-range": {
            "answer": {
                "id": "min-max-range",
                "type": "Number",
                "minimum": {
                    "value": {"identifier": "set-minimum", "source": "answers"}
                },
                "maximum": {
                    "value": {"identifier": "set-maximum", "source": "answers"}
                },
            }
        },
    }

    for value_source in value_sources:
        value_source_validator = ValueSourceValidator(
            value_source, "", questionnaire_schema
        )
        value_source_validator.validate()

    number_answer_validator = NumberAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )
    number_answer_validator.validate_referred_numeric_answer(
        questionnaire_schema.numeric_answer_ranges
    )

    min_max_range = questionnaire_schema.get_answer("min-max-range")
    min_max_minimum_value = min_max_range["minimum"]["value"]
    min_max_maximum_value = min_max_range["maximum"]["value"]

    assert min_max_minimum_value == value_sources[0]
    assert min_max_maximum_value == value_sources[1]

