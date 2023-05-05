from app.validators.blocks.grand_calculated_summary_block_validator import (
    GrandCalculatedSummaryBlockValidator,
)
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


def test_invalid_grand_calculated_summary():
    """Asserts invalid `when`:
    types, currencies or units are not of the same type for GrandCalculatedSummary
    or when there are duplicate calculated summaries in the calculation,
    or when there are two calculated summaries with a duplicate answer set
    or when a source in the calculation is not a calculated summary
    or when a calculated summary block id is invalid"""
    filename = "schemas/invalid/test_invalid_grand_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "message": GrandCalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_TYPE,
            "block_id": "grand-calculated-summary-type-error",
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_CURRENCY,
            "block_id": "grand-calculated-summary-currency-error",
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_UNIT,
            "block_id": "grand-calculated-summary-unit-error",
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARIES_HAS_DUPLICATES,
            "block_id": "grand-calculated-summary-duplicate-calculated-summary-error",
            "duplicates": ["calculated-number-1"],
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
            "block_id": "grand-calculated-summary-duplicate-answer-set-error",
            "duplicate_answers": ["calculated-unit-1", "calculated-unit-1-duplicate"],
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.GRAND_CALCULATED_SUMMARY_HAS_INVALID_SOURCE,
            "block_id": "grand-calculated-summary-source-error",
            "value_source": {"identifier": "q1-a1", "source": "answers"},
        },
        {
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_HAS_INVALID_ID,
            "block_id": "grand-calculated-summary-id-error",
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []
    for block_id in [
        "grand-calculated-summary-type-error",
        "grand-calculated-summary-currency-error",
        "grand-calculated-summary-unit-error",
        "grand-calculated-summary-duplicate-calculated-summary-error",
        "grand-calculated-summary-duplicate-answer-set-error",
        "grand-calculated-summary-source-error",
        "grand-calculated-summary-id-error",
    ]:
        block = questionnaire_schema.get_block(block_id)
        validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)
        errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_grand_calculated_summary_before_calculated_summary():
    """Asserts invalid `when` a grand calculated summary comes after a calculated summary it references"""
    filename = "schemas/invalid/test_invalid_grand_calculated_summary_before_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "calculated_summary_id": "calculated-currency-2",
            "block_id": "grand-calculated-summary-before-calculated-summary-error",
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY,
        }
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []

    block = questionnaire_schema.get_block(
        "grand-calculated-summary-before-calculated-summary-error"
    )
    validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)
    errors += validator.validate()

    assert errors == expected_error_messages
