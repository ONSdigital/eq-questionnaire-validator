import pytest

from app import error_messages
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.rules.rule_validator import RulesValidator
from app.validators.value_source_validator import ValueSourceValidator
from tests.conftest import get_mock_schema

ORIGIN_ID = "block-id"

default_answer_with_context = {
    "string-answer": {"answer": {"id": "string-answer", "type": "TextField"}}
}


def get_validator(
    rule,
    *,
    questionnaire_schema=None,
    answers_with_context=None,
    allow_self_reference=False,
):
    return RulesValidator(
        rule,
        ORIGIN_ID,
        get_mock_schema(questionnaire_schema, answers_with_context),
        allow_self_reference=allow_self_reference,
    )


@pytest.mark.parametrize(
    "operator_name, first_argument, second_argument",
    [
        ("==", {"source": "answers", "identifier": "string-answer"}, "Maybe"),
        ("==", "Maybe", {"source": "answers", "identifier": "string-answer"}),
        ("!=", {"source": "answers", "identifier": "string-answer"}, "Maybe"),
        ("!=", "Maybe", {"source": "answers", "identifier": "string-answer"}),
        ("in", {"source": "answers", "identifier": "string-answer"}, ["Maybe"]),
        ("in", "Maybe", {"source": "answers", "identifier": "array-answer"}),
        ("any-in", {"source": "answers", "identifier": "array-answer"}, ["Maybe"]),
        ("any-in", ["Maybe"], {"source": "answers", "identifier": "array-answer"}),
        ("all-in", {"source": "answers", "identifier": "array-answer"}, ["Maybe"]),
        ("all-in", ["Maybe"], {"source": "answers", "identifier": "array-answer"}),
    ],
)
def test_validate_options(operator_name, first_argument, second_argument):
    rule = {operator_name: [first_argument, second_argument]}

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "string-answer": {"answer": {"id": "string-answer", "type": "Radio"}},
        "array-answer": {"answer": {"id": "array-answer", "type": "Checkbox"}},
    }
    questionnaire_schema.answer_id_to_option_values_map = {
        "string-answer": ["Yes", "No"],
        "array-answer": ["Yes", "No"],
    }
    validator = get_validator(rule, questionnaire_schema=questionnaire_schema)
    validator.validate()

    expected_error = {
        "message": validator.VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS,
        "origin_id": ORIGIN_ID,
        "answer_options": ["Yes", "No"],
        "value": "Maybe",
    }

    assert validator.errors == [expected_error]


@pytest.mark.parametrize(
    "operator_name, first_argument, second_argument",
    [
        ("==", {"source": "answers", "identifier": "string-answer"}, None),
        ("!=", {"source": "answers", "identifier": "string-answer"}, None),
        ("in", {"source": "answers", "identifier": "string-answer"}, [None]),
        ("any-in", {"source": "answers", "identifier": "array-answer"}, [None]),
        ("all-in", [None], {"source": "answers", "identifier": "array-answer"}),
    ],
)
def test_validate_options_null_value_is_valid(
    operator_name, first_argument, second_argument
):
    rule = {operator_name: [first_argument, second_argument]}

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "string-answer": {"answer": {"id": "string-answer", "type": "Radio"}},
        "array-answer": {"answer": {"id": "array-answer", "type": "Checkbox"}},
    }
    questionnaire_schema.answer_id_to_option_values_map = {
        "string-answer": ["Yes", "No"],
        "array-answer": ["Yes", "No"],
    }
    validator = get_validator(rule, questionnaire_schema=questionnaire_schema)
    validator.validate()

    assert not validator.errors


def test_validate_options_multiple_errors():
    rule = {
        "in": [
            {"source": "answers", "identifier": "string-answer"},
            ["Maybe", "Not sure"],
        ]
    }

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "string-answer": {"answer": {"id": "string-answer", "type": "Radio"}}
    }
    questionnaire_schema.answer_id_to_option_values_map = {
        "string-answer": ["Yes", "No"]
    }
    validator = get_validator(rule, questionnaire_schema=questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": validator.VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS,
            "origin_id": ORIGIN_ID,
            "answer_options": ["Yes", "No"],
            "value": "Maybe",
        },
        {
            "message": validator.VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS,
            "origin_id": ORIGIN_ID,
            "answer_options": ["Yes", "No"],
            "value": "Not sure",
        },
    ]

    assert validator.errors == expected_errors


def test_validate_date_operator_non_date_answer():
    date_operator = {"date": [{"source": "answers", "identifier": "string-answer"}]}

    validator = get_validator(
        date_operator, answers_with_context=default_answer_with_context
    )
    validator.validate()

    expected_error = {
        "message": validator.DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER,
        "origin_id": ORIGIN_ID,
        "value_source": {"source": "answers", "identifier": "string-answer"},
    }

    assert validator.errors == [expected_error]


def test_validate_date_operator_with_offset():
    date_operator = {
        "date": [{"source": "answers", "identifier": "string-answer"}, {"years": 1}]
    }

    validator = get_validator(
        date_operator, answers_with_context=default_answer_with_context
    )
    validator.validate()

    expected_error = {
        "message": validator.DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER,
        "origin_id": ORIGIN_ID,
        "value_source": {"source": "answers", "identifier": "string-answer"},
    }

    assert validator.errors == [expected_error]


def test_validate_nested_date_operator_non_date_answer():
    rule = {
        "and": [
            {
                "==": [
                    {"date": [{"source": "answers", "identifier": "string-answer"}]},
                    {"date": ["2021-01-01"]},
                ]
            },
            {"==": [{"source": "answers", "identifier": "string-answer"}, "Yes"]},
        ]
    }

    validator = get_validator(rule, answers_with_context=default_answer_with_context)
    validator.validate()

    expected_error = {
        "message": validator.DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER,
        "origin_id": ORIGIN_ID,
        "value_source": {"source": "answers", "identifier": "string-answer"},
    }

    assert validator.errors == [expected_error]


def test_validate_count_operator_non_checkbox_answer():
    count_operator = {"count": [{"source": "answers", "identifier": "array-answer"}]}

    validator = get_validator(
        count_operator,
        answers_with_context={
            "array-answer": {"answer": {"id": "array-answer", "type": "TextField"}}
        },
    )
    validator.validate()

    expected_error = {
        "argument_type": "string",
        "argument_value": {"identifier": "array-answer", "source": "answers"},
        "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
        "operator": "count",
        "origin_id": "block-id",
        "valid_types": ["array"],
    }

    assert validator.errors == [expected_error]


def test_validate_sum_operator():
    sum_operator = {"+": [{"source": "answers", "identifier": "array-answer"}, 10]}

    validator = get_validator(
        sum_operator,
        answers_with_context={
            "array-answer": {"answer": {"id": "array-answer", "type": "TextField"}}
        },
    )
    validator.validate()

    expected_error = {
        "argument_type": "string",
        "argument_value": {"identifier": "array-answer", "source": "answers"},
        "message": validator.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
        "operator": "+",
        "origin_id": "block-id",
        "valid_types": ["number"],
    }

    assert validator.errors == [expected_error]


def test_validate_nested_sum_operator():
    sum_operator = {
        "+": [
            {
                "+": [
                    {"source": "answers", "identifier": "array-answer"},
                    {"source": "answers", "identifier": "checkbox-answer"},
                ]
            },
            {"source": "answers", "identifier": "number-answer"},
        ]
    }

    validator = get_validator(
        sum_operator,
        answers_with_context={
            "array-answer": {"answer": {"id": "array-answer", "type": "TextField"}},
            "checkbox-answer": {
                "answer": {"id": "checkbox-answer", "type": "Checkbox"}
            },
            "number-answer": {"answer": {"id": "array-answer", "type": "Number"}},
        },
    )
    validator.validate()

    expected_errors = [
        {
            "argument_type": "object",
            "argument_value": {
                "+": [
                    {"identifier": "array-answer", "source": "answers"},
                    {"identifier": "checkbox-answer", "source": "answers"},
                ]
            },
            "message": "Invalid argument type for operator",
            "operator": "+",
            "origin_id": "block-id",
            "valid_types": ["number"],
        },
    ]

    assert validator.errors == expected_errors


def test_map_operator_with_self_reference():
    operator = {
        "map": [
            {"format-date": [{"date": ["self"]}, "yyyy-MM-dd"]},
            {
                "date-range": [
                    {
                        "date": [
                            {"source": "response_metadata", "identifier": "started_at"}
                        ]
                    },
                    7,
                ]
            },
        ]
    }

    validator = get_validator(operator)
    validator.validate()

    assert not validator.errors


def test_map_operator_without_self_reference():
    operator = {
        "map": [
            {"format-date": [{"date": ["now"]}, "yyyy-MM-dd"]},
            {
                "date-range": [
                    {
                        "date": [
                            {"source": "response_metadata", "identifier": "started_at"}
                        ]
                    },
                    7,
                ]
            },
        ]
    }

    validator = get_validator(operator)
    validator.validate()

    expected_error = {
        "message": validator.MAP_OPERATOR_WITHOUT_SELF_REFERENCE,
        "origin_id": ORIGIN_ID,
        "rule": {"format-date": [{"date": ["now"]}, "yyyy-MM-dd"]},
    }

    assert validator.errors == [expected_error]


@pytest.mark.parametrize(
    "operator_name, operands",
    [
        ("date", ["self"]),
        ("format-date", ["self"]),
        ("format-date", [{"date": ["self"]}]),
    ],
)
def test_self_reference_outside_map_operator_without_allow_self_reference(
    operator_name, operands
):
    rule = {operator_name: operands}

    validator = get_validator(
        rule,
        answers_with_context={
            "date-answer": {"answer": {"id": "date-answer", "type": "Date"}}
        },
        allow_self_reference=False,
    )
    validator.validate()

    expected_error = {
        "message": validator.SELF_REFERENCE_OUTSIDE_MAP_OPERATOR,
        "origin_id": ORIGIN_ID,
        "rule": rule,
    }

    assert expected_error in validator.errors


@pytest.mark.parametrize(
    "operator_name, operands",
    [
        ("date", ["self"]),
        ("format-date", ["self"]),
        ("format-date", [{"date": ["self"]}]),
    ],
)
def test_self_reference_outside_map_operator_with_allow_self_reference(
    operator_name, operands
):
    rule = {operator_name: operands}

    validator = get_validator(rule, answers_with_context={}, allow_self_reference=True)
    validator.validate()

    assert not validator.errors


def test_non_existing_answer_id_in_option_label_for_value_operator():
    rule = {"option-label-from-value": ["self", "non-existing-answer"]}

    validator = get_validator(rule, answers_with_context={}, allow_self_reference=True)
    validator.validate()

    expected_error = {
        "message": ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
        "origin_id": ORIGIN_ID,
        "identifier": "non-existing-answer",
    }

    assert validator.errors == [expected_error]


def test_answer_type_invalid_for_option_label_from_value():
    rule = {"option-label-from-value": ["self", "string-answer"]}
    validator = get_validator(
        rule,
        answers_with_context=default_answer_with_context,
        allow_self_reference=True,
    )
    validator.validate()

    expected_error = {
        "message": error_messages.ANSWER_TYPE_FOR_OPTION_LABEL_FROM_VALUE_INVALID,
        "origin_id": ORIGIN_ID,
        "identifier": "string-answer",
    }

    assert validator.errors == [expected_error]
