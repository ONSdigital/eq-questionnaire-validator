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


def get_question_validator(question, data_version):
    validators = {
        "Calculated": CalculatedQuestionValidator,
        "DateRange": DateRangeQuestionValidator,
        "MutuallyExclusive": MutuallyExclusiveQuestionValidator,
    }
    return validators.get(question["type"], QuestionValidator)(question, data_version)
