from app.answer_type import AnswerType
from app.validators.validator import Validator


class AnswerValidator(Validator):
    OPTION_MISSING_Q_CODE = "Option q_code must be provided"
    ANSWER_MISSING_Q_CODE = "Answer q_code must be provided"
    DETAIL_ANSWER_MISSING_Q_CODE = "Detail answer q_code must be provided"
    CONFIRMATION_QUESTION_Q_CODE = "Confirmation question has q_code"

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

        if self.questionnaire_schema.schema["data_version"] != "0.0.1":
            return

        question_id = self.questionnaire_schema.get_block_id_by_answer_id(
            self.answer["id"]
        )

        if self.questionnaire_schema.get_block(question_id).get(
            "type"
        ) == "ConfirmationQuestion" and self.answer.get("q_code"):
            self.add_error(
                self.CONFIRMATION_QUESTION_Q_CODE, answer_id=self.answer["id"]
            )
        # No check in options as ConfirmationQuestion answer can be Radio type only and Radio options are already checked for q_code presence elsewhere

        if self.answer.get("q_code") and not self.answer.get("options"):
            return

        if not self.answer.get("q_code") and self.answer.get("type") != "Checkbox":
            self.add_error(self.ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"])

        if self.answer.get("options") and self.check_options():
            self.add_error(self.OPTION_MISSING_Q_CODE, answer_id=self.answer["id"])

    def check_options(self):
        for option in self.answer.get("options"):
            if (
                not option.get("q_code")
                and not option.get("detail_answer")
                and self.answer.get("type") != "Radio"
            ):

                return True
            if self.check_detail_answer(option):
                self.add_error(
                    self.DETAIL_ANSWER_MISSING_Q_CODE,
                    answer_id=self.answer["id"],
                )

    def check_detail_answer(self, option):
        if detail_answer := option.get("detail_answer"):
            if not detail_answer.get("q_code") and self.answer.get("type") == "Radio":
                return True
