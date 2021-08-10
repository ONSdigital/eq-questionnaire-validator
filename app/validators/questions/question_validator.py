from app.validators.validator import Validator


class QuestionValidator(Validator):
    question = {}

    def __init__(self, schema_element):
        super().__init__(schema_element)
        self.question = schema_element
        self.answers = self.question.get("answers", [])
        self.context["question_id"] = schema_element["id"]

    def validate(self):
        if self.question["type"] != "MutuallyExclusive":
            self._validate_answer_labels()

        return self.errors

    def _validate_answer_labels(self):
        if len(self.answers) < 2:
            return None

        for answer in self.answers:
            if not answer.get("label"):
                self.add_error(
                    "Answer label must be provided for questions with multiple answers",
                    answer_id=answer["id"],
                )
