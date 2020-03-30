from app.validation.answer_validator import AnswerValidator


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

    answer_validator = AnswerValidator(answer)

    answer_validator.validate_numeric_answer_decimals()

    assert answer_validator.errors[0] == {
        "message": AnswerValidator.DECIMAL_PLACES_TOO_LONG,
        "decimal_places": 10,
        "limit": 6,
        "id": "answer-5",
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

    answer_validator = AnswerValidator(answer)

    answer_validator.validate_numeric_answer_value()

    assert answer_validator.errors[0] == {
        "message": "Minimum value is less than system limit",
        "value": -99999999999,
        "limit": -999999999,
        "id": "answer-4",
    }

    assert answer_validator.errors[1] == {
        "message": "Maximum value is greater than system limit",
        "value": 99999999999,
        "limit": 9999999999,
        "id": "answer-4",
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

    answer_validator = AnswerValidator(answer)

    assert not answer_validator.is_offset_date_valid()


def test_invalid_answer_default():
    answer = {
        "default": 0,
        "id": "answer-7",
        "label": "Default with Mandatory",
        "mandatory": True,
        "type": "Number",
    }

    answer_validator = AnswerValidator(answer)
    answer_validator.validate()

    assert answer_validator.errors[0] == {
        "message": AnswerValidator.DEFAULT_ON_MANDATORY,
        "id": "answer-7",
    }


def test_invalid_url_in_answer():
    answer = {
        "id": "country-answer",
        "label": "What is your country of birth?",
        "mandatory": False,
        "suggestions_url": "this isn't a valid url",
        "type": "TextField",
    }

    answer_validator = AnswerValidator(answer)

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

    answer_validator = AnswerValidator(answer)
    answer_validator.validate()

    assert answer_validator.errors[0] == {
        "message": AnswerValidator.DECIMAL_PLACES_UNDEFINED,
        "id": "total-percentage",
    }


def test_unique_answer_options():
    answer = {
        "id": "duplicate-country-answer",
        "label": "",
        "type": "Checkbox",
        "options": [
          {
            "label": "India",
            "value": "India"
          },
          {
            "label": "Azerbaijan",
            "value": "Azerbaijan"
          },
          {
            "label": "India",
            "value": "India"
          },
          {
            "label": "Malta",
            "value": "Malta"
          }
        ]
      }

    answer_validator = AnswerValidator(answer)
    answer_validator.validate_duplicate_options()

    assert answer_validator.errors == [{
        "message": AnswerValidator.DUPLICATE_LABEL_FOUND,
        "id": "duplicate-country-answer",
        "label": "India"
    }, {
        "message": AnswerValidator.DUPLICATE_VALUE_FOUND,
        "id": "duplicate-country-answer",
        "value": "India"
    }]
