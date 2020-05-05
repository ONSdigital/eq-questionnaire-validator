from app.validation import error_messages
from app.validation.blocks.calculated_summary_block_validator import (
    CalculatedSummaryBlockValidator,
)
from app.validation.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = "schemas/invalid/test_invalid_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "message": error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_TYPE,
            "id": "total-playback-type-error",
        },
        {
            "message": error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_CURRENCY,
            "id": "total-playback-currency-error",
        },
        {
            "message": error_messages.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_UNIT,
            "id": "total-playback-unit-error",
        },
        {
            "message": error_messages.ANSWERS_TO_CALCULATE_HAS_INVALID_ID,
            "answer_id": "seventh-number-answer",
            "id": "total-playback-answer-error",
        },
        {
            "message": error_messages.ANSWERS_TO_CALCULATE_HAS_DUPLICATES,
            "id": "total-playback-duplicate-error",
            "duplicate_answers": {"sixth-number-answer", "fourth-number-answer"},
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []
    for block_id in [
        "total-playback-type-error",
        "total-playback-currency-error",
        "total-playback-unit-error",
        "total-playback-answer-error",
        "total-playback-duplicate-error",
    ]:
        block = questionnaire_schema.get_block(block_id)
        validator = CalculatedSummaryBlockValidator(block, questionnaire_schema)
        validator.validate()
        errors += validator.errors

    assert errors == expected_error_messages
