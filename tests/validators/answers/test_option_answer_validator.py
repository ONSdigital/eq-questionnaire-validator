from app.validators.answers import OptionAnswerValidator
from tests.conftest import get_mock_schema


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


def test_min_answer_options_without_dynamic_options():
    answer_type = "Checkbox"
    answer = {"id": "answer", "label": "Label", "type": answer_type, "options": []}

    validator = OptionAnswerValidator(answer)
    validator.validate_min_options()

    assert validator.errors == [
        {
            "message": validator.INVALID_NUMBER_OF_ANSWER_OPTIONS.format(
                answer_type=answer_type, required_num_options=1, actual_num_options=0
            ),
            "answer_id": "answer",
        }
    ]


def test_min_answer_options_with_dynamic_options():
    answer_type = "Checkbox"
    answer = {
        "id": "answer",
        "label": "Label",
        "type": answer_type,
        "options": [],
        "dynamic_options": {"values": {}, "transform": {}},
    }

    validator = OptionAnswerValidator(answer)
    validator.validate_min_options()

    assert validator.errors == [
        {"message": validator.OPTIONS_DEFINED_BUT_EMPTY, "answer_id": "answer"}
    ]


def test_dynamic_options_transform_allows_non_map_self_reference():
    answer = {
        "id": "answer",
        "label": "Label",
        "type": "Checkbox",
        "dynamic_options": {
            "values": {"source": "answers", "identifier": "checkbox-answer"},
            "transform": {"option-label-from-value": ["self", "checkbox-answer"]},
        },
    }

    validator = OptionAnswerValidator(
        answer,
        questionnaire_schema=get_mock_schema(
            answers_with_context={
                "checkbox-answer": {
                    "answer": {"id": "checkbox-answer", "type": "Checkbox"}
                }
            }
        ),
    )
    validator.validate_dynamic_options()

    assert not validator.errors
