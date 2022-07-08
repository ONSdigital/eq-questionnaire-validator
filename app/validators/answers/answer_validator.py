from app.answer_type import AnswerType
from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class AnswerValidator(Validator):
    OPTION_MISSING_Q_CODE = "Option q_code must be provided"
    ANSWER_MISSING_Q_CODE = "Answer q_code must be provided"
    DETAIL_ANSWER_MISSING_Q_CODE = "Detail answer q_code must be provided or removed"
    CONFIRMATION_QUESTION_Q_CODE = "Confirmation question has q_code"
    DATA_VERSION_0_0_3_Q_CODE_PRESENT = (
        "q_code can only be used with data_version 0.0.1"
    )

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
            has_q_code = get_object_containing_key(self.answer, key_name="q_code")
            if has_q_code:
                self.add_error(
                    self.DATA_VERSION_0_0_3_Q_CODE_PRESENT,
                    answer_id=self.answer["id"],
                )

            return None

        block_id = self.questionnaire_schema.get_block_id_by_answer_id(
            self.answer["id"]
        )
        is_confirmation_question = (
            self.questionnaire_schema.get_block(block_id).get("type")
            == "ConfirmationQuestion"
        )

        if is_confirmation_question:
            if self.answer.get("q_code"):
                self.add_error(
                    self.CONFIRMATION_QUESTION_Q_CODE, answer_id=self.answer["id"]
                )
                # No check in options as ConfirmationQuestion answer can be Radio type only and Radio options
                # are already checked for q_code presence elsewhere

        elif self.answer_type.value == "Checkbox":
            self._validate_checkbox_q_code()

        else:
            if not self.answer.get("q_code"):

                self.add_error(self.ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"])

            if self.answer.get("options") and self._validate_options_q_code():

                self.add_error(self.OPTION_MISSING_Q_CODE, answer_id=self.answer["id"])

    def _validate_options_q_code(self):
        for option in self.answer.get("options"):
            if (
                not option.get("q_code")
                and not option.get("detail_answer")
                and self.answer.get("type") != "Radio"
            ):

                return True
            if self._validate_detail_answer_q_code(option):
                self.add_error(
                    self.DETAIL_ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"]
                )

    def _validate_detail_answer_q_code(self, option):
        if detail_answer := option.get("detail_answer"):
            if not detail_answer.get("q_code") and self.answer_type.value == "Radio":
                return True
            if detail_answer.get("q_code") and self.answer_type.value == "Checkbox":
                return True

    def _validate_checkbox_q_code(self):
        if not self.answer.get("q_code"):
            if self.answer.get("options"):
                if self._validate_options_q_code():

                    self.add_error(
                        self.OPTION_MISSING_Q_CODE, answer_id=self.answer["id"]
                    )

            else:
                self.add_error(self.ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"])
