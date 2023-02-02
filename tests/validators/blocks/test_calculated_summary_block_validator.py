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
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_TYPE,
            "block_id": "total-playback-type-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_CURRENCY,
            "block_id": "total-playback-currency-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_UNIT,
            "block_id": "total-playback-unit-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_HAS_INVALID_ID,
            "answer_id": "seventh-number-answer",
            "block_id": "total-playback-answer-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_HAS_DUPLICATES,
            "block_id": "total-playback-duplicate-error",
            "duplicate_answers": ["fourth-number-answer", "sixth-number-answer"],
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_TYPE,
            "block_id": "total-playback-duplicate-error",
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
        errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_new_calculated_summary():
    """Asserts invalid `when` types, currencies or units are not of the same type for CalculatedSummary"""
    filename = "schemas/invalid/test_invalid_new_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_TYPE,
            "block_id": "total-playback-type-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_CURRENCY,
            "block_id": "total-playback-currency-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_UNIT,
            "block_id": "total-playback-unit-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_HAS_INVALID_ID,
            "answer_id": "seventh-number-answer",
            "block_id": "total-playback-answer-error",
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_HAS_DUPLICATES,
            "block_id": "total-playback-duplicate-error",
            "duplicate_answers": ["fourth-number-answer", "sixth-number-answer"],
        },
        {
            "message": CalculatedSummaryBlockValidator.ANSWERS_MUST_HAVE_SAME_TYPE,
            "block_id": "total-playback-duplicate-error",
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
        errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_calculated_summary_answer_after_calculated_summary_block():
    """Asserts invalid `when` answer id referenced in calculated summary comes after calculated summary block"""
    filename = "schemas/invalid/test_invalid_new_calculated_summary_answer_after_calculated_summary.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "block": {
                "calculation": {
                    "operation": {
                        "+": [
                            {"identifier": "first-number-answer", "source": "answers"},
                            {"identifier": "second-number-answer", "source": "answers"},
                            {
                                "identifier": "second-number-answer-also-in-total",
                                "source": "answers",
                            },
                            {"identifier": "third-number-answer", "source": "answers"},
                        ]
                    },
                    "title": "Grand total of previous values",
                },
                "id": "currency-total-playback",
                "title": "We calculate the total of currency values entered to be "
                "%(total)s. Is this correct? (Skipped Fourth)",
                "type": "CalculatedSummary",
            },
            "block_id": "currency-total-playback",
            "message": CalculatedSummaryBlockValidator.ANSWER_SET_AFTER_CALCULATED_SUMMARY,
        }
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []

    block = questionnaire_schema.get_block("currency-total-playback")
    validator = CalculatedSummaryBlockValidator(block, questionnaire_schema)
    errors += validator.validate()

    assert errors == expected_error_messages


def test_invalid_calculated_summary_answer_in_different_section():
    """Asserts invalid `when` answer id referenced is in a different section to the calculated summary block"""
    filename = "schemas/invalid/test_invalid_new_calculated_summary_answer_in_different_section.json"
    json_to_validate = _open_and_load_schema_file(filename)

    expected_error_messages = [
        {
            "block_id": "currency-total-playback",
            "section_ids": {"section-1", "section-2"},
            "message": CalculatedSummaryBlockValidator.ANSWER_SET_IN_DIFFERENT_SECTION_FOR_CALCULATED_SUMMARY,
        }
    ]

    questionnaire_schema = QuestionnaireSchema(json_to_validate)
    errors = []

    block = questionnaire_schema.get_block("currency-total-playback")
    validator = CalculatedSummaryBlockValidator(block, questionnaire_schema)
    errors += validator.validate()

    assert errors == expected_error_messages
