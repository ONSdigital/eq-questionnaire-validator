"""Tests for the validation of answers to calculate in calculated questions."""

from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.questions import get_question_validator
from tests.utils import _open_and_load_schema_file


def test_missing_id_in_answers_to_calculate():
    """Check that answers_to_calculate contains an answer_id that exists in the question."""
    filename = "schemas/invalid/test_invalid_calculations_value_source.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    question = schema.blocks_by_id["breakdown-block"]["question"]

    validator = get_question_validator(question, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_NOT_IN_QUESTION,
            "question_id": "breakdown-question",
            "answer_id": "breakdown-3",
        },
        {
            "message": validator.ANSWER_NOT_IN_QUESTION,
            "question_id": "breakdown-question",
            "answer_id": "breakdown-4",
        },
    ]

    assert expected_error_messages == validator.errors


def test_invalid_answer_type_in_answers_to_calculate():
    """Check non-numeric answer types are invalid when all answer types match."""
    filename = "schemas/invalid/test_invalid_calculations_value_source.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    question = schema.blocks_by_id["additional-breakdown-block"]["question"]

    validator = get_question_validator(question, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string",
            ),
            "answer_id": "total-answer",
            "question_id": "additional-breakdown-question",
        },
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string",
            ),
            "answer_id": "additional-breakdown-1",
            "question_id": "additional-breakdown-question",
        },
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string",
            ),
            "answer_id": "additional-breakdown-2",
            "question_id": "additional-breakdown-question",
        },
    ]

    assert expected_error_messages == validator.errors


def test_invalid_answer_type_in_answers_to_calculate_against_numeric_value():
    """Validate answers_to_calculate contains only numeric values independent of whether answer_id exists."""
    filename = "schemas/invalid/test_invalid_calculations_value_source.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    question = schema.blocks_by_id["text-breakdown-block"]["question"]

    validator = get_question_validator(question, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string",
            ),
            "answer_id": "text-breakdown-1",
            "question_id": "text-breakdown-question",
        },
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string",
            ),
            "answer_id": "text-breakdown-2",
            "question_id": "text-breakdown-question",
        },
    ]

    assert expected_error_messages == validator.errors


def test_answers_to_calculate_too_short():
    """Check that answers_to_calculate is not too short."""
    filename = (
        "schemas/invalid/test_invalid_validation_sum_against_total_dynamic_answers.json"
    )
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    question = schema.blocks_by_id["dynamic-answer-only"]["question"]

    validator = get_question_validator(question, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWERS_TO_CALCULATE_TOO_SHORT.format(
                list=["percentage-of-shopping-elsewhere"],
            ),
            "question_id": "dynamic-answer-only-question",
        },
    ]

    assert expected_error_messages == validator.errors


def test_invalid_different_numeric_answer_types():
    """Validation for answers to calculate that have a different type to the answer_id they are being calculated against."""
    filename = "schemas/invalid/test_invalid_validation_sum_against_total_different_answer_types.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    question = schema.blocks_by_id["breakdown-block"]["question"]
    validator = get_question_validator(question, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_TYPES_FOR_CALCULATION_MISMATCH.format(
                answer_types=["Currency", "Number"],
            ),
            "question_id": "breakdown-question",
        },
    ] * 2  # calculation with answer_id and value_source both exhibit the error

    assert expected_error_messages == validator.errors
