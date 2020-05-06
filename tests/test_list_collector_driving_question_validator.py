from app.validation import error_messages
from app.validation.blocks.list_collector_driving_question_validator import (
    ListCollectorDrivingQuestionValidator,
)
from app.validation.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_driving_question_multiple_collectors():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_collectors.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("anyone-usually-live-at")
    validator = ListCollectorDrivingQuestionValidator(block, questionnaire_schema)

    expected_error_message = [
        {
            "message": error_messages.MULTIPLE_LIST_COLLECTORS_FOR_DRIVING_QUESTION,
            "block_id": "anyone-usually-live-at",
            "list_name": "people",
        }
    ]

    validator.validate()

    assert expected_error_message == validator.errors


def test_invalid_driving_question_multiple_driving_questions():
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_driving_questions.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("anyone-usually-live-at")
    validator = ListCollectorDrivingQuestionValidator(block, questionnaire_schema)

    expected_error_messages = [
        {
            "message": error_messages.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
            "block_id": "anyone-usually-live-at",
            "for_list": "people",
        }
    ]

    validator.validate()

    assert expected_error_messages == validator.errors
