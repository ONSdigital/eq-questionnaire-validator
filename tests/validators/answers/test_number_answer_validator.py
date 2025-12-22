import pytest  # pyright: ignore

from app.validators.answers import NumberAnswerValidator
from app.validators.questionnaire_schema import (
    MAX_NUMBER,
    MIN_NUMBER,
    QuestionnaireSchema,
)
from tests.conftest import get_mock_schema_with_data_version
from tests.utils import _open_and_load_schema_file


def test_minimum_value():
    answer = {
        "id": "answer-4",
        "label": "Max/Min out of system limits",
        "mandatory": False,
        "maximum": {"value": 9_999_999_999_999_999},
        "minimum": {"value": -9_999_999_999_999_999},
        "type": "Number",
    }

    validator = NumberAnswerValidator(answer, questionnaire_schema={})

    validator.validate_value_in_limits()

    assert validator.errors[0] == {
        "message": validator.MINIMUM_LESS_THAN_LIMIT,
        "value": -9_999_999_999_999_999,
        "limit": MIN_NUMBER,
        "answer_id": "answer-4",
    }

    assert validator.errors[1] == {
        "message": validator.MAXIMUM_GREATER_THAN_LIMIT,
        "value": 9_999_999_999_999_999,
        "limit": MAX_NUMBER,
        "answer_id": "answer-4",
    }


def test_invalid_answer_default():
    answer = {
        "default": 0,
        "id": "answer-7",
        "label": "Default with Mandatory",
        "mandatory": True,
        "type": "Number",
    }

    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )
    validator.validate_mandatory_has_no_default()

    assert validator.errors[0] == {
        "message": validator.DEFAULT_ON_MANDATORY,
        "answer_id": "answer-7",
    }


def test_are_decimal_places_valid():
    answer = {
        "calculated": True,
        "description": "The total percentages should be 100%",
        "id": "total-percentage",
        "label": "Total",
        "mandatory": False,
        "q_code": "10002",
        "type": "Percentage",
        "maximum": {"value": 100},
    }

    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )
    validator.validate_decimal_places()

    assert validator.errors[0] == {
        "message": validator.DECIMAL_PLACES_UNDEFINED,
        "answer_id": "total-percentage",
    }


@pytest.mark.parametrize(
    "bounds, error_count",
    [
        ({"minimum": {"value": "100"}}, 1),
        ({"maximum": {"value": "0"}}, 1),
        ({"maximum": {"value": "100"}, "minimum": {"value": "0"}}, 2),
    ],
)
def test_invalid_min_or_max_is_string(bounds, error_count):
    answer = {
        "calculated": True,
        "description": "The total percentages should be 100%",
        "id": "total-percentage",
        "label": "Total",
        "mandatory": False,
        "q_code": "10002",
        "type": "Percentage",
        **bounds,
    }

    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )
    validator.validate_min_max_is_number()

    assert validator.errors[0] == {
        "message": validator.MIN_OR_MAX_IS_NOT_NUMERIC,
        "answer_id": "total-percentage",
    }
    assert len(validator.errors) == error_count


def test_valid_minimum_value_is_float():
    answer = {
        "id": "answer-2",
        "mandatory": True,
        "type": "Currency",
        "label": "Money spent on vegetables",
        "description": "Enter the full value",
        "minimum": {"value": 0.00, "exclusive": True},
    }

    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )

    validator.validate_min_max_is_number()

    assert len(validator.errors) == 0


def test_valid_max_if_numeric_value_source():
    filename = "schemas/valid/test_calculated_summary.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer = schema.get_answer("set-maximum-answer")

    validator = NumberAnswerValidator(answer, schema)

    validator.validate_min_max_is_number()

    assert len(validator.errors) == 0


def test_invalid_range():
    answer = {
        "id": "answer-3",
        "label": "Invalid References",
        "mandatory": False,
        "maximum": {"value": {"identifier": "answer-5", "source": "answers"}},
        "minimum": {"value": {"identifier": "answer-4", "source": "answers"}},
        "type": "Percentage",
    }
    answers = {"answers": [answer]}
    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )

    questionnaire_schema = QuestionnaireSchema(answers)

    validator.validate_referred_numeric_answer(
        questionnaire_schema.numeric_answer_ranges,
    )

    expected_errors = [
        {
            "message": validator.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-4",
            "answer_id": "answer-3",
        },
        {
            "message": validator.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-5",
            "answer_id": "answer-3",
        },
    ]

    assert validator.errors == expected_errors


def test_invalid_range_calculated_summary_source():
    filename = "schemas/invalid/test_invalid_calculated_summary_answer_ranges.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer = schema.get_answer("set-minimum-answer")

    validator = NumberAnswerValidator(
        answer,
        get_mock_schema_with_data_version("0.0.3"),
    )

    validator.validate_referred_numeric_answer(schema.numeric_answer_ranges)

    expected_errors = [
        {
            "message": validator.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "currency-total-playback",
            "answer_id": "set-minimum-answer",
        },
        {
            "message": validator.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "currency-total-playback",
            "answer_id": "set-minimum-answer",
        },
    ]

    assert validator.errors == expected_errors


def test_invalid_numeric_answers():
    validator = NumberAnswerValidator(
        {
            "decimal_places": 2,
            "id": "answer-1",
            "label": "Answer 1",
            "mandatory": False,
            "type": "Number",
        },
        get_mock_schema_with_data_version("0.0.3"),
    )
    validator.validate_referred_numeric_answer_decimals(
        {
            "answer-1": {
                "min_referred": "answer-2",
                "max_referred": None,
                "decimal_places": 2,
            },
            "answer-2": {"decimal_places": 3},
        },
    )

    expected_errors = [
        {
            "message": validator.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
            "referenced_id": "answer-2",
            "answer_id": "answer-1",
        },
    ]

    assert validator.errors == expected_errors


def test_invalid_maximum_minimum_value_from_answer_source():
    answer = {
        "id": "min-max-range",
        "mandatory": False,
        "minimum": {"value": {"identifier": "set-minimum", "source": "answers"}},
        "maximum": {"value": {"identifier": "set-maximum", "source": "answers"}},
        "type": "Number",
    }

    answers = {
        "answers": [
            answer,
            {
                "id": "set-minimum",
                "type": "Number",
                "minimum": {"value": -9_999_999_999_999_999},
            },
            {
                "id": "set-maximum",
                "type": "Number",
                "maximum": {"value": 9_999_999_999_999_999},
            },
        ],
    }

    questionnaire_schema = QuestionnaireSchema(answers)

    validator = NumberAnswerValidator(answer, questionnaire_schema)

    validator.validate_value_in_limits()

    expected_errors = [
        {
            "message": validator.MINIMUM_LESS_THAN_LIMIT,
            "value": -9_999_999_999_999_999,
            "limit": MIN_NUMBER,
            "answer_id": "min-max-range",
        },
        {
            "message": validator.MAXIMUM_GREATER_THAN_LIMIT,
            "value": 9_999_999_999_999_999,
            "limit": MAX_NUMBER,
            "answer_id": "min-max-range",
        },
    ]

    assert validator.errors == expected_errors
