from app.validators.answers import NumberAnswerValidator


def test_minimum_value():
    answer = {
        "id": "answer-4",
        "label": "Max/Min out of system limits",
        "mandatory": False,
        "maximum": {"value": 99999999999},
        "minimum": {"value": -99999999999},
        "type": "Number",
    }

    validator = NumberAnswerValidator(answer)

    validator.validate_value_in_limits()

    assert validator.errors[0] == {
        "message": validator.MINIMUM_LESS_THAN_LIMIT,
        "value": -99999999999,
        "limit": -999999999,
        "answer_id": "answer-4",
    }

    assert validator.errors[1] == {
        "message": validator.MAXIMUM_GREATER_THAN_LIMIT,
        "value": 99999999999,
        "limit": 9999999999,
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

    validator = NumberAnswerValidator(answer)
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

    validator = NumberAnswerValidator(answer)
    validator.validate_decimal_places()

    assert validator.errors[0] == {
        "message": validator.DECIMAL_PLACES_UNDEFINED,
        "answer_id": "total-percentage",
    }


def test_invalid_range():
    answer = {
        "id": "answer-3",
        "label": "Invalid References",
        "mandatory": False,
        "maximum": {"value": {"identifier": "answer-5", "source": "answers"}},
        "minimum": {"value": {"identifier": "answer-4", "source": "answers"}},
        "type": "Percentage",
    }
    validator = NumberAnswerValidator(answer)

    validator.validate_referred_numeric_answer({"answer-3": {"min": None, "max": None}})

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


def test_invalid_numeric_answers():
    validator = NumberAnswerValidator(
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
            "message": validator.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
            "referenced_id": "answer-2",
            "answer_id": "answer-1",
        }
    ]

    assert validator.errors == expected_errors
