from unittest.mock import Mock

import pytest

from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.types import (
    TYPE_ARRAY,
    TYPE_BOOLEAN,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_OBJECT,
    TYPE_STRING,
    python_type_to_json_type,
    resolve_value_source_json_type,
)
from tests.test_questionnaire_validator import _open_and_load_schema_file


@pytest.mark.parametrize(
    "python_type, json_type",
    [
        ("dict", TYPE_OBJECT),
        ("list", TYPE_ARRAY),
        ("str", TYPE_STRING),
        ("int", TYPE_NUMBER),
        ("float", TYPE_NUMBER),
        ("bool", TYPE_BOOLEAN),
        ("NoneType", TYPE_NULL),
    ],
)
def test_get_answer_value_json_type(python_type, json_type):
    assert python_type_to_json_type(python_type) == json_type


@pytest.mark.parametrize(
    "answer_type, json_type",
    [
        ("Address", TYPE_OBJECT),
        ("Duration", TYPE_OBJECT),
        ("Relationship", TYPE_OBJECT),
        ("Checkbox", TYPE_ARRAY),
        ("Date", TYPE_STRING),
        ("MonthYearDate", TYPE_STRING),
        ("YearDate", TYPE_STRING),
        ("Dropdown", TYPE_STRING),
        ("MobileNumber", TYPE_STRING),
        ("Radio", TYPE_STRING),
        ("TextArea", TYPE_STRING),
        ("TextField", TYPE_STRING),
        ("Currency", TYPE_NUMBER),
        ("Number", TYPE_NUMBER),
        ("Percentage", TYPE_NUMBER),
        ("Unit", TYPE_NUMBER),
    ],
)
def test_resolve_answer_value_source_json_type(answer_type, json_type):
    value_source = {"source": "answers", "identifier": "answer-1"}

    questionnaire_schema = Mock()
    questionnaire_schema.answers_with_context = {
        "answer-1": {"answer": {"id": "answer-1", "type": answer_type}, "block": "name"}
    }

    assert (
        resolve_value_source_json_type(value_source, questionnaire_schema) == json_type
    )


def test_resolve_calculated_summary_value_source_json_type():
    filename = "schemas/valid/test_routing_calculated_summary_dependencies.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    value_source = {
        "source": "calculated_summary",
        "identifier": "currency-total-playback",
    }

    assert (
        resolve_value_source_json_type(value_source, questionnaire_schema)
        == TYPE_NUMBER
    )


@pytest.mark.parametrize(
    "source, selector, json_type",
    [
        ("metadata", None, TYPE_STRING),
        ("location", None, TYPE_STRING),
        ("list", "count", TYPE_NUMBER),
        ("list", "first", TYPE_STRING),
        ("list", "primary_person", TYPE_STRING),
        ("list", "same_name_items", TYPE_ARRAY),
        ("list", None, TYPE_ARRAY),
    ],
)
def test_resolve_non_answer_value_source_json_type(source, selector, json_type):
    value_source = {"source": source}
    if selector:
        value_source["selector"] = selector
    assert resolve_value_source_json_type(value_source, {}) == json_type
