from app.validators.validator import Validator


class QuestionValidator(Validator):
    ANSWER_LABEL_MISSING_MULTIPLE_ANSWERS = (
        "Answer label must be provided for questions with multiple answers"
    )
    ANSWER_Q_CODE_MISSING = "Answer q_code must be provided"
    question = {}

    def __init__(self, schema_element, data_version):
        super().__init__(schema_element)
        self.question = schema_element
        self.answers = self.question.get("answers", [])
        self.context["question_id"] = schema_element["id"]
        self.data_version = data_version

    def validate(self):
        if self.question["type"] != "MutuallyExclusive":
            self._validate_answer_labels()
        if self.data_version == "0.0.1":
            self._validate_q_codes()

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

    def _validate_q_codes(self):
        for answer in self.answers:
            if answer.get("options") and answer.get("type") != "Radio":
                for option in answer.get("options"):
                    if not option.get("q_code"):
                        self.add_error(
                            self.ANSWER_Q_CODE_MISSING, answer_id=answer["id"]
                        )
            elif not answer.get("q_code"):
                self.add_error(self.ANSWER_Q_CODE_MISSING, answer_id=answer["id"])
