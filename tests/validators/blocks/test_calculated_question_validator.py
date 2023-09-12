from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.questions import get_question_validator
from tests.utils import _open_and_load_schema_file


def test_invalid_id_in_answers_to_calculate():
    filename = "schemas/invalid/test_invalid_calculations_value_source.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    question = {
        "id": "breakdown-question",
        "title": "Breakdown validated against an answer value source",
        "description": [
            "This is a breakdown of the total number from the previous question."
        ],
        "type": "Calculated",
        "calculations": [
            {
                "calculation_type": "sum",
                "value": {"source": "answers", "identifier": "total-answer"},
                "answers_to_calculate": [
                    "breakdown-1",
                    "breakdown-2",
                    "breakdown-3",
                    "breakdown-4",
                ],
                "conditions": ["equals"],
            }
        ],
        "answers": [
            {
                "id": "breakdown-1",
                "label": "Breakdown 1",
                "mandatory": False,
                "decimal_places": 2,
                "type": "Number",
            },
            {
                "id": "breakdown-2",
                "label": "Breakdown 2",
                "mandatory": False,
                "decimal_places": 2,
                "type": "Number",
            },
        ],
    }

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
        {
            "message": validator.ANSWER_TYPE_FOR_CALCULATION_TYPE_INVALID.format(
                answer_type="string"
            ),
            "referenced_answer": "total-answer",
            "question_id": "breakdown-question",
        },
    ]

    assert expected_error_messages == validator.errors


def test_answers_to_calculate_too_short():
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
                list=["percentage-of-shopping-elsewhere"]
            ),
            "question_id": "dynamic-answer-only-question",
        }
    ]

    assert expected_error_messages == validator.errors


def test_invalid_different_numeric_answer_types():
    """
    Validation for answers to calculate that have a different type to the answer_id they are being calculated against
    """
    filename = "schemas/invalid/test_invalid_validation_sum_against_total_different_answer_types.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    errors: list[dict] = []

    for block_id in ["breakdown-block", "additional-breakdown-block"]:
        question = schema.blocks_by_id[block_id]["question"]
        validator = get_question_validator(question, schema)
        validator.validate()
        errors.extend(validator.errors)

    expected_error_messages = [
        {
            "message": validator.ANSWER_TYPES_FOR_CALCULATION_MISMATCH.format(
                answer_types=["Currency", "Number"]
            ),
            "question_id": "breakdown-question",
            "referenced_answer": "total-answer",
        },
        {
            "message": validator.ANSWER_TYPES_FOR_CALCULATION_MISMATCH.format(
                answer_types=["Currency", "Number"]
            ),
            "question_id": "additional-breakdown-question",
            "referenced_answer": "total-answer",
        },
    ]

    assert expected_error_messages == errors
