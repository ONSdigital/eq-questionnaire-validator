import pytest

from app.validators.questionnaire_schema import QuestionnaireSchema
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
        "message": validator.COUNT_OPERATOR_REFERENCES_NON_CHECKBOX_ANSWER,
        "origin_id": ORIGIN_ID,
        "value_source": {"source": "answers", "identifier": "array-answer"},
    }

    assert validator.errors == [expected_error]


def test_map_operator_with_self_reference():
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

    validator = get_validator(
        operator,
        answers_with_context={
            "date-answer": {"answer": {"id": "date-answer", "type": "Date"}}
        },
    )
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
def test_self_reference_outside_map_operator(operator_name, operands):
    rule = {operator_name: operands}

    validator = get_validator(
        rule,
        answers_with_context={
            "date-answer": {"answer": {"id": "date-answer", "type": "Date"}}
        },
    )
    validator.validate()

    expected_error = {
        "message": validator.SELF_REFERENCE_OUTSIDE_MAP_OPERATOR,
        "origin_id": ORIGIN_ID,
        "rule": rule,
    }

    assert expected_error in validator.errors
