from app.validation.questions.calculated_question_validator import (
    CalculatedQuestionValidator,
)
from app.validation.questions.date_range_question_validator import (
    DateRangeQuestionValidator,
)
from app.validation.questions.mutually_exclusive_validator import (
    MutuallyExclusiveQuestionValidator,
)
from app.validation.questions.question_validator import QuestionValidator


def get_question_validator(question):
    validators = {
        "Calculated": CalculatedQuestionValidator,
        "DateRange": DateRangeQuestionValidator,
        "MutuallyExclusive": MutuallyExclusiveQuestionValidator,
    }
    return validators.get(question["type"], QuestionValidator)(question)
