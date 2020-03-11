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

    errors = answer_validator.validate_numeric_answer_decimals()

    assert errors == [
        'Number of decimal places 10 for answer "answer-5" is greater than system limit '
        "of 6"
    ]


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

    errors = answer_validator.validate_numeric_answer_value()

    assert errors == [
        'Minimum value -99999999999 for answer "answer-4" is less than system limit of '
        "-999999999",
        'Maximum value 99999999999 for answer "answer-4" is greater than system limit of '
        "9999999999",
    ]


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
    errors = answer_validator.validate_numeric_default()

    assert errors == ["Default is being used with a mandatory answer: answer-7"]
