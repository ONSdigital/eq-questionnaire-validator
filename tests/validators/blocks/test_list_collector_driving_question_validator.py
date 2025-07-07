"""Test for ListCollectorDrivingQuestionValidator to ensure it correctly identifies invalid configurations of driving questions in list collectors."""

from app.validators.blocks.list_collector_driving_question_validator import (
    ListCollectorDrivingQuestionValidator,
)
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


def test_invalid_driving_question_multiple_driving_questions():
    """Test that a list collector with multiple driving questions raises the correct error."""
    filename = "schemas/invalid/test_invalid_list_collector_driving_question_multiple_driving_questions.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("anyone-usually-live-at")
    validator = ListCollectorDrivingQuestionValidator(block, questionnaire_schema)

    expected_error_messages = [
        {
            "message": validator.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
            "block_id": "anyone-usually-live-at",
            "for_list": "people",
        },
    ]

    assert expected_error_messages == validator.validate()
