from app import error_messages
from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.answers.text_field_answer_validator import TextFieldAnswerValidator


def test_invalid_mismatching_answer_label_and_value():
    answer = {
        "type": "Radio",
        "id": "correct-answer",
        "mandatory": False,
        "options": [
            {"label": "Yes it is {name}", "value": "Yes it is"},
            {"label": "Nope", "value": "No"},
        ],
    }

    expected_errors = [
        "Found mismatching answer value for label: Yes it is {name} in answer id: correct-answer",
        "Found mismatching answer value for label: Nope in answer id: correct-answer",
    ]

    answer_validator = AnswerValidator(answer)

    errors = answer_validator.validate_labels_and_values_match()

    assert expected_errors == errors


def test_number_of_decimals():
    answer = {
        "decimal_places": 10,
        "id": "answer-5",
        "label": "Too many decimals declared",
        "mandatory": False,
        "type": "Number",
    }

    answer_validator = NumberAnswerValidator(answer)

    answer_validator.validate_numeric_answer_decimals()

    assert answer_validator.errors[0] == {
        "message": error_messages.DECIMAL_PLACES_TOO_LONG,
        "decimal_places": 10,
        "limit": 6,
        "answer_id": "answer-5",
    }


def test_minimum_value():
    answer = {
        "id": "answer-4",
        "label": "Max/Min out of system limits",
        "mandatory": False,
        "maximum": {"value": 99999999999},
        "minimum": {"value": -99999999999},
        "type": "Number",
    }

    answer_validator = NumberAnswerValidator(answer)

    answer_validator.validate_numeric_answer_value()

    assert answer_validator.errors[0] == {
        "message": "Minimum value is less than system limit",
        "value": -99999999999,
        "limit": -999999999,
        "answer_id": "answer-4",
    }

    assert answer_validator.errors[1] == {
        "message": "Maximum value is greater than system limit",
        "value": 99999999999,
        "limit": 9999999999,
        "answer_id": "answer-4",
    }


def test_invalid_single_date_period():
    answer = {
        "id": "date-range-from",
        "label": "Period from",
        "mandatory": True,
        "maximum": {"offset_by": {"days": 2}, "value": "2017-06-11"},
        "minimum": {"offset_by": {"days": -19}, "value": "now"},
        "type": "Date",
    }

    answer_validator = DateAnswerValidator(answer)

    assert not answer_validator.is_offset_date_valid()


def test_invalid_answer_default():
    answer = {
        "default": 0,
        "id": "answer-7",
        "label": "Default with Mandatory",
        "mandatory": True,
        "type": "Number",
    }

    answer_validator = NumberAnswerValidator(answer)
    answer_validator.validate()

    assert answer_validator.errors[0] == {
        "message": error_messages.DEFAULT_ON_MANDATORY,
        "answer_id": "answer-7",
    }


def test_invalid_url_in_answer():
    answer = {
        "id": "country-answer",
        "label": "What is your country of birth?",
        "mandatory": False,
        "suggestions_url": "this isn't a valid url",
        "type": "TextField",
    }

    answer_validator = TextFieldAnswerValidator(answer)

    assert not answer_validator.is_suggestion_url_valid()


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

    answer_validator = NumberAnswerValidator(answer)
    answer_validator.validate()

    assert answer_validator.errors[0] == {
        "message": error_messages.DECIMAL_PLACES_UNDEFINED,
        "answer_id": "total-percentage",
    }


def test_unique_answer_options():
    answer = {
        "id": "duplicate-country-answer",
        "label": "",
        "type": "Checkbox",
        "options": [
            {"label": "India", "value": "India"},
            {"label": "Azerbaijan", "value": "Azerbaijan"},
            {"label": "India", "value": "India"},
            {"label": "Malta", "value": "Malta"},
        ],
    }

    answer_validator = AnswerValidator(answer)
    answer_validator.validate_duplicate_options()

    assert answer_validator.errors == [
        {
            "message": error_messages.DUPLICATE_LABEL_FOUND,
            "answer_id": "duplicate-country-answer",
            "label": "India",
        },
        {
            "message": error_messages.DUPLICATE_VALUE_FOUND,
            "answer_id": "duplicate-country-answer",
            "value": "India",
        },
    ]


def test_invalid_range():
    answer = {
        "id": "answer-3",
        "label": "Invalid References",
        "mandatory": False,
        "maximum": {"value": {"identifier": "answer-5", "source": "answers"}},
        "minimum": {"value": {"identifier": "answer-4", "source": "answers"}},
        "type": "Percentage",
    }
    validator = AnswerValidator(answer)

    validator.validate_referred_numeric_answer({"answer-3": {"min": None, "max": None}})

    expected_errors = [
        {
            "message": error_messages.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-4",
            "answer_id": "answer-3",
        },
        {
            "message": error_messages.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-5",
            "answer_id": "answer-3",
        },
    ]

    assert validator.errors == expected_errors


def test_invalid_numeric_answers():
    validator = AnswerValidator(
        {
            "decimal_places": 2,
            "id": "answer-1",
            "label": "Answer 1",
            "mandatory": False,
            "type": "Number",
        }
    )
    validator.validate_referred_numeric_answer_decimals(
        {
            "answer-1": {
                "min_referred": "answer-2",
                "max_referred": None,
                "decimal_places": 2,
            },
            "answer-2": {"decimal_places": 3},
        }
    )

    expected_errors = [
        {
            "message": error_messages.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
            "referenced_id": "answer-2",
            "answer_id": "answer-1",
        }
    ]

    assert validator.errors == expected_errors
