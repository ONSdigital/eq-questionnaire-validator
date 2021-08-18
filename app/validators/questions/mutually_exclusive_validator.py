from app.validators.questions.question_validator import QuestionValidator


class MutuallyExclusiveQuestionValidator(QuestionValidator):
    question = {}
    MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY = (
        "MutuallyExclusive question type cannot contain mandatory answers."
    )
    NON_CHECKBOX_ANSWER = "Question is not of type Checkbox."

    def validate(self):
        super().validate()

        if any(answer["mandatory"] is True for answer in self.answers):
            self.add_error(self.MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY)

        if self.answers[-1]["type"] != "Checkbox":
            self.add_error(self.NON_CHECKBOX_ANSWER, answer_id=self.answers[-1]["id"])
        return self.errors
