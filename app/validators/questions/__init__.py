from app.validators.questions.calculated_question_validator import (
    CalculatedQuestionValidator,
)
from app.validators.questions.date_range_question_validator import (
    DateRangeQuestionValidator,
)
from app.validators.questions.mutually_exclusive_validator import (
    MutuallyExclusiveQuestionValidator,
)
from app.validators.questions.question_validator import QuestionValidator


def get_question_validator(question, schema):
    """Factory function called by section validator to return the appropriate question validator based on
    the question type. If question type doesn't match keys in validators dict, it returns a default `QuestionValidator`,
    no schema needed for general question validation.

    Args:
        question (dict): The question to be validated.
        schema (QuestionnaireSchema): The entire questionnaire schema, which may be needed for certain validators.

    Returns:
        An instance of a question validator class that corresponds to the type of the question.
    """
    if question["type"] == "Calculated":
        validators = {
            "Calculated": CalculatedQuestionValidator,
        }
        return validators.get(question["type"], QuestionValidator)(question, schema)
    validators = {
        "DateRange": DateRangeQuestionValidator,
        "MutuallyExclusive": MutuallyExclusiveQuestionValidator,
    }
    return validators.get(question["type"], QuestionValidator)(question)
