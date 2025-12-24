from app.validators.blocks.grand_calculated_summary_block_validator import (
    GrandCalculatedSummaryBlockValidator,
)
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


def test_invalid_grand_calculated_summary():
    """Asserts invalid `when`.

    types, currencies or units are not of the same type for GrandCalculatedSummary
    or when there are duplicate calculated summaries in the calculation,
    or when there are two calculated summaries with a duplicate answer set
    or when a source in the calculation is not a calculated summary
    or when a calculated summary block id is invalid
    """
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
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_WITH_DUPLICATE_ANSWERS,
            "block_id": "grand-calculated-summary-duplicate-answer-set-error",
            "duplicate_answers": ["calculated-unit-1", "calculated-unit-1-duplicate"],
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
        "grand-calculated-summary-duplicate-answer-set-error",
        "grand-calculated-summary-id-error",
    ]:
        block = questionnaire_schema.get_block(block_id)
        # Block always exists in this test schema, .get_block() will never return None
        validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)  # type: ignore
        errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_grand_calculated_summary_before_calculated_summary():
    """Asserts invalid `when` a grand calculated summary comes after a calculated summary it references."""
    filename = "schemas/invalid/test_invalid_grand_calculated_summary_before_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "calculated_summary_id": "calculated-currency-2",
            "block_id": "grand-calculated-summary-before-calculated-summary-error",
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_AFTER_GRAND_CALCULATED_SUMMARY,
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []

    block = questionnaire_schema.get_block(
        "grand-calculated-summary-before-calculated-summary-error",
    )
    # Block always exists in this test schema, .get_block() will never return None
    validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)  # type: ignore
    errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_repeating_grand_calculated_summary_referencing_repeating_calculated_summary():
    """Asserts `invalid` when a repeating GCS references a repeating CS from a different repeating section."""
    filename = "schemas/invalid/test_invalid_grand_calculated_summary_inside_repeating_section.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "calculated_summary_id": "calculated-summary-base-cost",
            "block_id": "grand-calculated-summary-vehicle",
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_IN_DIFFERENT_REPEATING_SECTION,
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    # Block always exists in this test schema, .get_block() will never return None
    block = questionnaire_schema.get_block("grand-calculated-summary-vehicle")  # type: ignore
    # Validator always instantiates for this test schema (block always exists)
    validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)  # type: ignore
    errors = validator.validate()

    assert errors == expected_error_messages


def test_invalid_non_repeating_grand_calculated_summary_referencing_repeating_calculated_summary():
    """Asserts `invalid` when a non-repeating GCS references a repeating CS."""
    filename = "schemas/invalid/test_invalid_grand_calculated_summary_inside_repeating_section.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "calculated_summary_id": "calculated-summary-base-cost",
            "block_id": "grand-calculated-invalid-outside-repeat",
            "message": GrandCalculatedSummaryBlockValidator.REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT,
        },
        {
            "calculated_summary_id": "calculated-summary-running-cost",
            "block_id": "grand-calculated-invalid-outside-repeat",
            "message": GrandCalculatedSummaryBlockValidator.REPEATING_CALCULATED_SUMMARY_OUTSIDE_REPEAT,
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    # Block always exists in this test schema, .get_block() will never return None
    block = questionnaire_schema.get_block("grand-calculated-invalid-outside-repeat")  # type: ignore
    # Validator always instantiates for this test schema (block always exists)
    validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)  # type: ignore
    errors = validator.validate()

    assert errors == expected_error_messages


def test_invalid_repeating_grand_calculated_summary_with_repeating_answers_in_calculated_summary():
    """Asserts `invalid` when a repeating GCS references a static CS that has repeating answers for the same list.

    You can't have a calculated summary of add/edit-block answers. So dynamic & repeating block covers all scenarios
    """
    filename = "schemas/invalid/test_invalid_grand_calculated_summary_with_repeating_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "calculated_summary_id": "calculated-summary-permit-cost",
            "block_id": "grand-calculated-summary-repeating-answer-cs",
            "list_name": "vehicles",
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_WITH_REPEATING_ANSWERS_FOR_SAME_LIST,
        },
        {
            "calculated_summary_id": "calculated-summary-tax-cost",
            "block_id": "grand-calculated-summary-dynamic-answer-cs",
            "list_name": "vehicles",
            "message": GrandCalculatedSummaryBlockValidator.CALCULATED_SUMMARY_WITH_REPEATING_ANSWERS_FOR_SAME_LIST,
        },
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []
    for block_id in [
        "grand-calculated-summary-repeating-answer-cs",
        "grand-calculated-summary-dynamic-answer-cs",
    ]:
        # Block always exists in this test schema, .get_block() will never return None
        block = questionnaire_schema.get_block(block_id)  # type: ignore
        # Validator always instantiates for this test schema (block always exists)
        validator = GrandCalculatedSummaryBlockValidator(block, questionnaire_schema)  # type: ignore
        errors += validator.validate()

    assert errors == expected_error_messages
