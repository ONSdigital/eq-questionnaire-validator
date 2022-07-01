from app.answer_type import AnswerType
from app.validators.validator import Validator


class AnswerValidator(Validator):
    OPTION_MISSING_Q_CODE = "Option q_code must be provided"
    ANSWER_MISSING_Q_CODE = "Answer q_code must be provided"
    DETAIL_ANSWER_MISSING_Q_CODE = "Detail answer q_code must be provided"

    def __init__(self, schema_element, questionnaire_schema):
        super().__init__(schema_element)
        self.answer = schema_element
        self.answer_id = self.answer["id"]
        self.answer_type = AnswerType(self.answer["type"])
        self.context["answer_id"] = self.answer_id
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        self._validate_q_codes()

        return self.errors

    def _validate_q_codes(self):
        if self.questionnaire_schema.schema["data_version"] != "0.0.1" or (
            self.answer.get("q_code") and not self.answer.get("options")
        ):
            return

        if not self.answer.get("q_code") and self.answer.get("type") != "Checkbox":
            self.add_error(self.ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"])
            return

        if self.answer.get("options"):
            for option in self.answer.get("options"):
                if (
                    not option.get("q_code")
                    and not option.get("detail_answer")
                    and self.answer.get("type") != "Radio"
                ):
                    self.add_error(
                        self.OPTION_MISSING_Q_CODE, answer_id=self.answer["id"]
                    )
                    return
                if detail_answer := option.get("detail_answer"):
                    if (
                        not detail_answer.get("q_code")
                        and self.answer.get("type") == "Radio"
                    ):
                        self.add_error(
                            self.DETAIL_ANSWER_MISSING_Q_CODE,
                            answer_id=self.answer["id"],
                        )
