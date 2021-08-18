from app.validators.answers import OptionAnswerValidator


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

    validator = OptionAnswerValidator(answer)

    expected_errors = [
        {
            "message": validator.ANSWER_LABEL_VALUE_MISMATCH,
            "answer_id": "correct-answer",
            "label": "Yes it is {name}",
            "value": "Yes it is",
        },
        {
            "message": validator.ANSWER_LABEL_VALUE_MISMATCH,
            "answer_id": "correct-answer",
            "label": "Nope",
            "value": "No",
        },
    ]

    validator.validate_labels_and_values_match()

    assert expected_errors == validator.errors


def test_unique_answer_options():
    answer = {
        "id": "duplicate-country-answer",
        "label": "Label",
        "type": "Checkbox",
        "options": [
            {"label": "India", "value": "India"},
            {"label": "Azerbaijan", "value": "Azerbaijan"},
            {"label": "India", "value": "India"},
            {"label": "Malta", "value": "Malta"},
        ],
    }

    validator = OptionAnswerValidator(answer)
    validator.validate_duplicate_options()

    assert validator.errors == [
        {
            "message": validator.DUPLICATE_LABEL,
            "answer_id": "duplicate-country-answer",
            "label": "India",
        },
        {
            "message": validator.DUPLICATE_VALUE,
            "answer_id": "duplicate-country-answer",
            "value": "India",
        },
    ]


def test_validate_default_exists_in_options():
    answer = {
        "type": "Radio",
        "id": "correct-answer",
        "mandatory": False,
        "default": "Yes",
        "options": [
            {"label": "Yes it is", "value": "Yes it is"},
            {"label": "No", "value": "No"},
        ],
    }

    validator = OptionAnswerValidator(answer)

    expected_errors = [
        {
            "message": validator.ANSWER_DEFAULT_MISSING,
            "default_value": "Yes",
            "answer_id": "correct-answer",
        }
    ]

    validator.validate_default_exists_in_options()

    assert expected_errors == validator.errors
