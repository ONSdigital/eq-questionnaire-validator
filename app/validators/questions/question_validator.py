from app.validators.validator import Validator


class QuestionValidator(Validator):
    ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS = (
        "Answer label must be provided for questions with multiple answers"
    )
    question = {}

    def __init__(self, schema_element, schema=None):
        super().__init__(schema_element)
        self.question = schema_element
        self.answers = self.question.get("answers", [])
        self.context["question_id"] = schema_element["id"]
        self.schema = schema

    def validate(self):
        if self.question["type"] != "MutuallyExclusive":
            self._validate_answer_labels()

        return self.errors

    def _validate_answer_labels(self):
        if len(self.answers) < 2 or (
            len(self.answers) == 2
            and self.answers[-1]["type"] == "Checkbox"
            and len(self.answers[-1]["options"]) == 1
        ):
            return None

        for answer in self.answers:
            if not answer.get("label"):
                self.add_error(
                    self.ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS, answer_id=answer["id"]
                )
