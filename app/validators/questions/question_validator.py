from app.validators.validator import Validator


class QuestionValidator(Validator):
    ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS = (
        "Answer label must be provided for questions with multiple answers"
    )
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

        final_answer_single_checkbox = self.answers[1]["type"] == "Checkbox"
        for answer in self.answers:
            if not (
                len(self.answers) == 2 and final_answer_single_checkbox
            ) and not answer.get("label"):
                self.add_error(
                    self.ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS, answer_id=answer["id"]
                )
