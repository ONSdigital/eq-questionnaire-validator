from app.validators.questionnaire_schema import find_duplicates
from app.validators.validator import Validator


class AnswerCodeValidator(Validator):
    INCORRECT_DATA_VERSION_FOR_ANSWER_CODES = (
        "Answer codes are only supported in data version 0.0.3"
    )
    DUPLICATE_ANSWER_CODE_FOUND = "Answer codes must be unique"
    MISSING_ANSWER_CODE = "No answer codes found for answer_id set in the schema"
    ANSWER_CODE_ANSWER_ID_NOT_FOUND_IN_SCHEMA = (
        "No matching answer id found in the schema for the given answer code"
    )
    ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS = "Number of answer codes does not match number of answers for an answer with multiple options"
    MORE_THAN_ONE_ANSWER_CODE_SET_FOR_ANSWER_OPTIONS = "Only one answer code should be set for answers with answer options if not specifying a value"
    INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS = (
        "Values specified in answer code and answer options do not match"
    )

    def __init__(self, data_version, answer_codes, questionnaire_schema):
        self.data_version = data_version
        self.answer_codes = answer_codes
        self.questionnaire_schema = questionnaire_schema
        self.codes = [answer["code"] for answer in self.answer_codes]
        self.answer_codes_answer_ids = {
            answer["answer_id"] for answer in self.answer_codes
        }
        super().__init__(questionnaire_schema)

    def validate(self):
        self.validate_data_version()
        self.validate_duplicate_answer_codes()
        self.validate_missing_answer_id()
        self.validate_missing_answer_codes()
        self.validate_answer_codes_at_option_level()
        return self.errors

    def validate_data_version(self):
        if self.data_version != "0.0.3":
            self.add_error(self.INCORRECT_DATA_VERSION_FOR_ANSWER_CODES)

    def validate_duplicate_answer_codes(self):
        duplicates = find_duplicates(self.codes)

        if len(duplicates) > 0:
            self.add_error(self.DUPLICATE_ANSWER_CODE_FOUND, duplicates=duplicates)

    def validate_missing_answer_id(self):
        all_answer_ids = list(self.questionnaire_schema.answers_with_context)

        for answer_code_id in self.answer_codes_answer_ids:
            if answer_code_id not in all_answer_ids:
                self.add_error(
                    self.ANSWER_CODE_ANSWER_ID_NOT_FOUND_IN_SCHEMA,
                    answer_id=answer_code_id,
                )

    def validate_missing_answer_codes(self):
        all_answer_ids = list(self.questionnaire_schema.answers_with_context)

        for answer_id in all_answer_ids:
            if answer_id not in self.answer_codes_answer_ids:
                self.add_error(self.MISSING_ANSWER_CODE, answer_id=answer_id)

    def validate_answer_codes_at_option_level(self):
        answers_with_context = self.questionnaire_schema.answers_with_context

        for answer_id in answers_with_context:
            answer = answers_with_context[answer_id]

            if "options" in answer["answer"]:
                values = []
                values.extend(option["value"] for option in answer["answer"]["options"])

                answer_codes_for_options = [
                    answer_code
                    for answer_code in self.answer_codes
                    if answer_code["answer_id"] == answer_id
                ]

                if len(values) != len(answer_codes_for_options) and all(
                    "value" in answer_code for answer_code in answer_codes_for_options
                ):
                    self.add_error(
                        self.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
                        answer_options=answer["answer"]["options"],
                        answer_codes_for_options=answer_codes_for_options,
                    )

                for answer_code in answer_codes_for_options:
                    if answer_code.get("value") and answer_code["value"] not in values:
                        self.add_error(
                            self.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
                            value=answer_code["value"],
                            answer_codes_for_options=answer_codes_for_options,
                        )

                if len(answer_codes_for_options) != 1 and any(
                    "value" not in answer_code
                    for answer_code in answer_codes_for_options
                ):
                    self.add_error(
                        self.MORE_THAN_ONE_ANSWER_CODE_SET_FOR_ANSWER_OPTIONS,
                        answer_options=answer["answer"]["options"],
                        answer_codes_for_options=answer_codes_for_options,
                    )
