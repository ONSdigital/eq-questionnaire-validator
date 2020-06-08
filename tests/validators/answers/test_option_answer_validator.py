from app.validators.answers import OptionAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


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
        "label": "",
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
            "message": validator.FOUND_DUPLICATE_LABEL,
            "answer_id": "duplicate-country-answer",
            "label": "India",
        },
        {
            "message": validator.FOUND_DUPLICATE_VALUE,
            "answer_id": "duplicate-country-answer",
            "value": "India",
        },
    ]


def test_invalid_answer_action():
    filename = (
        "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_question.json"
    )
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = questionnaire_schema.get_answer("anyone-else-live-here-answer")
    validator = OptionAnswerValidator(answer, questionnaire_schema)

    expected_error_messages = [
        {
            "message": validator.LIST_NAME_MISSING,
            "answer_id": "anyone-else-live-here-answer",
            "list_name": "non-existent-list-name",
        },
        {
            "message": validator.BLOCK_ID_MISSING,
            "block_id": "non-existent-block-id",
            "answer_id": "anyone-else-live-here-answer",
        },
    ]

    validator.validate()

    assert expected_error_messages == validator.errors
