from app.validators.questions.question_validator import QuestionValidator


class CalculatedQuestionValidator(QuestionValidator):
    ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"

    def validate(self):
        super().validate()
        return self.errors
