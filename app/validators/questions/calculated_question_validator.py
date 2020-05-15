from app.validators.questions.question_validator import QuestionValidator


class CalculatedQuestionValidator(QuestionValidator):
    def validate(self):
        """
        Validates that any answer ids within the 'answer_to_group'
        list are existing answers within the question
        """
        answer_ids = [answer["id"] for answer in self.question.get("answers")]
        for calculation in self.question.get("calculations"):
            for answer_id in calculation["answers_to_calculate"]:
                if answer_id not in answer_ids:
                    self.add_error(
                        "Answer does not exist within this question",
                        answer_id=answer_id,
                    )
