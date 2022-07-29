from app.answer_type import AnswerType
from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class AnswerValidator(Validator):
    OPTION_MISSING_Q_CODE = "Option q_code must be provided"
    ANSWER_MISSING_Q_CODE = "Answer q_code must be provided"
    NON_CHECKBOX_OPTION_HAS_Q_CODE = "Non checkbox option cannot contain q_code"
    DETAIL_ANSWER_MISSING_Q_CODE = "Detail answer q_code must be provided"
    CHECKBOX_DETAIL_ANSWER_HAS_Q_CODE = "Checkbox detail answer cannot contain q_code"
    CONFIRMATION_QUESTION_HAS_Q_CODE = "Confirmation question cannot contain q_code"
    DATA_VERSION_NOT_0_0_1_Q_CODE_PRESENT = (
        "q_code can only be used with data_version 0.0.1"
    )
    CHECKBOX_ANSWER_AND_OPTIONS_Q_CODE_MUTUALLY_EXCLUSIVE = (
        "Checkbox answer and option q_code are mutually exclusive"
    )
    CHECKBOX_ANSWER_OR_OPTIONS_MUST_HAVE_Q_CODES = (
        "Either checkbox answer or options must have q_codes"
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
        is_confirmation_question = (
            self.questionnaire_schema.get_block_by_answer_id(self.answer_id).get("type")
            == "ConfirmationQuestion"
        )

        if (
            self.questionnaire_schema.schema["data_version"] != "0.0.1"
            or is_confirmation_question
        ):
            has_q_code = get_object_containing_key(self.answer, key_name="q_code")
            if has_q_code:
                self.add_error(
                    self.CONFIRMATION_QUESTION_HAS_Q_CODE
                    if is_confirmation_question
                    else self.DATA_VERSION_NOT_0_0_1_Q_CODE_PRESENT,
                    answer_id=self.answer["id"],
                )

            return None

        if self.answer_type is AnswerType.CHECKBOX:
            self._validate_checkbox_q_code()

        else:
            if not self.answer.get("q_code"):

                self.add_error(self.ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"])

            if self.answer.get("options") and self._validate_options_q_code():

                self.add_error(self.OPTION_MISSING_Q_CODE, answer_id=self.answer["id"])

    def _validate_options_q_code(self):
        any_option_missing_q_code = False
        for option in self.answer.get("options", []):
            option_has_q_code = option.get("q_code")
            is_checkbox = self.answer_type is AnswerType.CHECKBOX

            if is_checkbox:
                if not option_has_q_code:
                    any_option_missing_q_code = True
            elif option_has_q_code:
                self.add_error(
                    self.NON_CHECKBOX_OPTION_HAS_Q_CODE, answer_id=self.answer["id"]
                )

            if self._validate_detail_answer_q_code(option):
                self.add_error(
                    self.DETAIL_ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"]
                )

        return any_option_missing_q_code

    def _validate_detail_answer_q_code(self, option):
        if detail_answer := option.get("detail_answer"):
            has_q_code = detail_answer.get("q_code")
            is_checkbox = self.answer_type is AnswerType.CHECKBOX
            if is_checkbox:
                if has_q_code:
                    self.add_error(
                        self.CHECKBOX_DETAIL_ANSWER_HAS_Q_CODE,
                        answer_id=self.answer["id"],
                    )
            elif not has_q_code:
                self.add_error(
                    self.DETAIL_ANSWER_MISSING_Q_CODE, answer_id=self.answer["id"]
                )

    def _validate_checkbox_q_code(self):
        has_answer_q_code = self.answer.get("q_code")
        any_option_missing_q_code = self._validate_options_q_code()

        if has_answer_q_code:
            any_option_has_q_code = any(
                True for option in self.answer.get("options", []) if "q_code" in option
            )
            if any_option_has_q_code:
                self.add_error(
                    self.CHECKBOX_ANSWER_AND_OPTIONS_Q_CODE_MUTUALLY_EXCLUSIVE,
                    answer_id=self.answer["id"],
                )
        elif any_option_missing_q_code:
            self.add_error(
                self.CHECKBOX_ANSWER_OR_OPTIONS_MUST_HAVE_Q_CODES,
                answer_id=self.answer["id"],
            )
