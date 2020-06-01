from app.validators.questions.calculated_question_validator import (
    CalculatedQuestionValidator,
)


def test_invalid_id_in_answers_to_calculate():
    question = {
        "answers": [
            {
                "decimal_places": 2,
                "id": "breakdown-1",
                "label": "Breakdown 1",
                "type": "Number",
            },
            {
                "decimal_places": 2,
                "id": "breakdown-2",
                "label": "Breakdown 2",
                "type": "Number",
            },
        ],
        "calculations": [
            {
                "answer_id": "total-answer",
                "answers_to_calculate": [
                    "breakdown-1",
                    "breakdown-2",
                    "breakdown-3",
                    "breakdown-4",
                ],
                "calculation_type": "sum",
                "conditions": ["equals"],
            }
        ],
        "id": "breakdown-question",
        "title": "Breakdown",
        "type": "Calculated",
    }
    validator = CalculatedQuestionValidator(question)
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
