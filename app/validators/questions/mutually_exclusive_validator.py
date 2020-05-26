from app import error_messages
from app.validators.questions.question_validator import QuestionValidator


class MutuallyExclusiveQuestionValidator(QuestionValidator):
    question = {}

    def validate(self):
        answers = self.question["answers"]

        if any(answer["mandatory"] is True for answer in answers):
            self.add_error(error_messages.MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY)

        if answers[-1]["type"] != "Checkbox":
            self.add_error(
                error_messages.NON_CHECKBOX_ANSWER, answer_id=answers[-1]["id"]
            )
        return self.errors
