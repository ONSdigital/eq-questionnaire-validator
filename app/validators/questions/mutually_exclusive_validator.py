from app.answer_type import AnswerType
from app.validators.questions.question_validator import QuestionValidator


class MutuallyExclusiveQuestionValidator(QuestionValidator):
    question = {}
    MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY = (
        "MutuallyExclusive question type cannot contain mandatory answers."
    )
    INVALID_EXCLUSIVE_ANSWER = (
        "Mutually exclusive answer is not of type Checkbox or Radio."
    )
    NON_EXCLUSIVE_RADIO_ANSWER = (
        "Mutually exclusive questions cannot contain non exclusive Radio answers."
    )

    def validate(self):
        super().validate()

        if any(answer["mandatory"] is True for answer in self.answers):
            self.add_error(self.MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY)

        if AnswerType(self.answers[-1]["type"]) not in {
            AnswerType.CHECKBOX,
            AnswerType.RADIO,
        }:
            self.add_error(
                self.INVALID_EXCLUSIVE_ANSWER, answer_id=self.answers[-1]["id"]
            )

        if any(
            (AnswerType(answer["type"]) == AnswerType.RADIO)
            for answer in self.answers[:-1]
        ):
            self.add_error(self.NON_EXCLUSIVE_RADIO_ANSWER)
        return self.errors
