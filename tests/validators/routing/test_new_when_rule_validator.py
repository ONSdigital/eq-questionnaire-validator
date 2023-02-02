import pytest

from app.validators.routing.types import (
    TYPE_ARRAY,
    TYPE_DATE,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_OBJECT,
    TYPE_STRING,
)
from app.validators.rules.rule_validator import RulesValidator
from tests.conftest import get_mock_schema

ORIGIN_ID = "block-id"

default_answer_with_context = {
    "string-answer": {"answer": {"id": "string-answer", "type": "TextField"}}
}


def get_validator(rule, *, questionnaire_schema=None, answers_with_context=None):
    return RulesValidator(
        rule, ORIGIN_ID, get_mock_schema(questionnaire_schema, answers_with_context)
    )


@pytest.mark.parametrize(
    "first_argument, second_argument, types",
    [
        (1, {"date": ["2021-01-01"]}, [TYPE_NUMBER, TYPE_DATE]),
        ({"date": ["2021-01-01"]}, 1, [TYPE_DATE, TYPE_NUMBER]),
        (
            {"date": [{"source": "answers", "identifier": "date-answer"}]},
            1,
            [TYPE_DATE, TYPE_NUMBER],
        ),
        (
            1,
            {"date": [{"source": "answers", "identifier": "date-answer"}]},
            [TYPE_NUMBER, TYPE_DATE],
        ),
    ],
)
@pytest.mark.parametrize("operator_name", ["<", "<=", ">", ">="])
def test_operator_argument_type_mismatch(
    first_argument, second_argument, types, operator_name
):
    rule = {operator_name: [first_argument, second_argument]}

    validator = get_validator(
        rule,
        answers_with_context={
            "date-answer": {"answer": {"id": "date-answer", "type": "Date"}}
        },
    )
    validator.validate()

    expected_error = {
        "message": validator.OPERATOR_ARGUMENT_TYPE_MISMATCH,
        "origin_id": ORIGIN_ID,
        "rule": str(rule),
        "argument_types": types,
    }
    assert validator.errors == [expected_error]


@pytest.mark.parametrize(
    "first_argument, second_argument, types",
    [
        (1, "test", [TYPE_NUMBER, TYPE_STRING]),
        ("test", 1, [TYPE_STRING, TYPE_NUMBER]),
        (1, {"date": ["2021-01-01"]}, [TYPE_NUMBER, TYPE_DATE]),
        (
            1,
            {"source": "answers", "identifier": "string-answer"},
            [TYPE_NUMBER, TYPE_STRING],
        ),
    ],
)
@pytest.mark.parametrize("operator_name", ["!=", "=="])
def test_equality_operator_argument_type_mismatch(
    first_argument, second_argument, types, operator_name
):
    rule = {operator_name: [first_argument, second_argument]}

    validator = get_validator(
        rule,
        answers_with_context={
            "string-answer": {"answer": {"id": "answer-1", "type": "TextField"}}
        },
    )
    validator.validate()

    expected_error = {
        "message": validator.OPERATOR_ARGUMENT_TYPE_MISMATCH,
        "origin_id": ORIGIN_ID,
        "rule": str(rule),
        "argument_types": types,
    }
    assert validator.errors == [expected_error]


@pytest.mark.parametrize("first_argument, second_argument", [(1, None), (None, 1)])
@pytest.mark.parametrize("operator_name", ["!=", "=="])
def test_equality_operator_allows_null_mismatch(
    first_argument, second_argument, operator_name
):
    rule = {operator_name: [first_argument, second_argument]}

    validator = get_validator(rule)
    validator.validate()

    assert not validator.errors


@pytest.mark.parametrize(
    "rule",
    [
        ({"or": [{"==": [1, 1]}, {"==": [1, "Yes"]}]}),
        ({"and": [{"or": [{"==": [1, 1]}, {"==": [1, "Yes"]}]}, {"!=": [1, 2]}]}),
    ],
)
def test_operator_argument_type_mismatch_nested(rule):
    validator = get_validator(rule)
    validator.validate()

    expected_error = {
        "message": validator.OPERATOR_ARGUMENT_TYPE_MISMATCH,
        "origin_id": ORIGIN_ID,
        "rule": "{'==': [1, 'Yes']}",
        "argument_types": [TYPE_NUMBER, TYPE_STRING],
    }

    assert validator.errors == [expected_error]


@pytest.mark.parametrize("operator_name", ["==", "!=", "<", "<=", ">", ">="])
def test_comparison_operator_invalid_argument_types(operator_name):
    rule = {
        operator_name: [
            {"source": "answers", "identifier": "object-answer"},
            {"line1": "7 Evelyn Street"},
        ]
    }

    validator = get_validator(
        rule,
        answers_with_context={
            "object-answer": {"answer": {"id": "object-answer", "type": "Address"}}
        },
    )
    validator.validate()

    if operator_name in ["==", "!="]:
        valid_types = [TYPE_DATE, TYPE_NUMBER, TYPE_STRING, TYPE_NULL, TYPE_ARRAY]
    else:
        valid_types = [TYPE_DATE, TYPE_NUMBER]

    expected_errors = [
        {
            "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
            "origin_id": ORIGIN_ID,
            "argument_type": TYPE_OBJECT,
            "argument_value": {"identifier": "object-answer", "source": "answers"},
            "operator": operator_name,
            "valid_types": valid_types,
        },
        {
            "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
            "origin_id": ORIGIN_ID,
            "argument_type": TYPE_OBJECT,
            "argument_value": {"line1": "7 Evelyn Street"},
            "operator": operator_name,
            "valid_types": valid_types,
        },
    ]

    assert validator.errors == expected_errors


def test_in_operator_first_argument_is_not_array():
    rule = {"in": [{"source": "answers", "identifier": "array-answer"}, ["test"]]}

    validator = get_validator(
        rule,
        answers_with_context={
            "array-answer": {"answer": {"id": "array-answer", "type": "Checkbox"}}
        },
    )
    validator.validate()

    expected_error = {
        "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
        "origin_id": ORIGIN_ID,
        "argument_value": {"identifier": "array-answer", "source": "answers"},
        "argument_type": TYPE_ARRAY,
        "operator": "in",
        "valid_types": [TYPE_NUMBER, TYPE_STRING],
    }

    assert validator.errors == [expected_error]


def test_in_operator_second_argument_is_array():
    rule = {"in": ["test", {"source": "answers", "identifier": "string-answer"}]}

    validator = get_validator(rule, answers_with_context=default_answer_with_context)
    validator.validate()

    expected_error = {
        "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
        "origin_id": ORIGIN_ID,
        "argument_value": {"identifier": "string-answer", "source": "answers"},
        "argument_type": TYPE_STRING,
        "operator": "in",
        "valid_types": [TYPE_ARRAY],
    }

    assert validator.errors == [expected_error]


@pytest.mark.parametrize("operator_name", ["any-in", "all-in"])
def test_any_in_all_in_operators_arguments_not_arrays(operator_name):
    rule = {
        operator_name: [
            {"source": "answers", "identifier": "string-answer-1"},
            {"source": "answers", "identifier": "string-answer-2"},
        ]
    }

    validator = get_validator(
        rule,
        answers_with_context={
            "string-answer-1": {
                "answer": {"id": "string-answer-1", "type": "TextField"}
            },
            "string-answer-2": {
                "answer": {"id": "string-answer-2", "type": "TextField"}
            },
        },
    )
    validator.validate()

    expected_errors = [
        {
            "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
            "origin_id": ORIGIN_ID,
            "argument_value": {"identifier": "string-answer-1", "source": "answers"},
            "argument_type": TYPE_STRING,
            "operator": operator_name,
            "valid_types": [TYPE_ARRAY],
        },
        {
            "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
            "origin_id": ORIGIN_ID,
            "argument_value": {"identifier": "string-answer-2", "source": "answers"},
            "argument_type": TYPE_STRING,
            "operator": operator_name,
            "valid_types": [TYPE_ARRAY],
        },
    ]

    assert validator.errors == expected_errors


@pytest.mark.parametrize(
    "operator_name, first_argument, second_argument",
    [
        ("==", {"source": "answers", "identifier": "string-answer"}, "Yes"),
        ("==", {"source": "metadata", "identifier": "metadata_string"}, "Test String"),
        ("==", {"source": "list", "identifier": "a-list", "selector": "count"}, 1),
        (
            "==",
            {"source": "list", "identifier": "a-list", "selector": "first"},
            "list-item-id",
        ),
        (
            "==",
            {"source": "list", "identifier": "a-list", "selector": "primary_person"},
            "list-item-id",
        ),
        ("in", "list-item-id", {"source": "list", "identifier": "no-selector"}),
        (
            "in",
            "list-item-id",
            {"source": "list", "identifier": "a-list", "selector": "same_name_items"},
        ),
        ("==", {"source": "location", "identifier": "list_item_id"}, "list-item-id"),
    ],
)
def test_validate_value_sources(operator_name, first_argument, second_argument):
    rule = {operator_name: [first_argument, second_argument]}

    validator = get_validator(rule, answers_with_context=default_answer_with_context)
    validator.validate()

    assert not validator.errors
