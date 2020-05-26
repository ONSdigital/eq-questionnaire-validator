from app.validators.blocks.calculated_summary_block_validator import (
    CalculatedSummaryBlockValidator,
)
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = "schemas/invalid/test_invalid_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_TYPE,
            "block_id": "total-playback-type-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_CURRENCY,
            "block_id": "total-playback-currency-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_UNIT,
            "block_id": "total-playback-unit-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_TO_CALCULATE_HAS_INVALID_ID,
            "answer_id": "seventh-number-answer",
            "block_id": "total-playback-answer-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_TO_CALCULATE_HAS_DUPLICATES,
            "block_id": "total-playback-duplicate-error",
            "duplicate_answers": ["fourth-number-answer", "sixth-number-answer"],
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
