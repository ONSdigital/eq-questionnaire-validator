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
    question = {
        "answers": [
            {
                "label": {
                    "text": "Percentage of shopping elsewhere",
                    "placeholders": [
                        {
                            "placeholder": "transformed_value",
                            "value": {
                                "source": "answers",
                                "identifier": "supermarket-name",
                            },
                        }
                    ],
                },
                "id": "percentage-of-shopping-elsewhere",
                "mandatory": False,
                "type": "Percentage",
                "maximum": {"value": 100},
                "decimal_places": 0,
            }
        ],
        "calculations": [
            {
                "calculation_type": "sum",
                "value": 1000,
                "answers_to_calculate": ["percentage-of-shopping-elsewhere"],
                "conditions": ["equals"],
            }
        ],
        "id": "dynamic-answer-only-question",
        "type": "Calculated",
    }

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
