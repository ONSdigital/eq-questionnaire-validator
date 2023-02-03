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
    ANSWER_VALUE_SET_FOR_ANSWER_WITH_NO_OPTIONS = (
        "Answer values can only be set for answers that support answer options"
    )
    ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS = "Number of answer codes does not match number of answers for an answer with multiple options"
    MORE_THAN_ONE_ANSWER_CODE_SET_AT_PARENT_LEVEL = "Only one answer code should be set for an answer when not specifying answer codes for answer options"
    INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS = (
        "Values specified in answer code and answer options do not match"
    )
    DYNAMIC_ANSWER_OPTION_MUST_HAVE_ANSWER_CODE_SET_AT_TOP_LEVEL = (
        "Dynamic options must have an answer code set at the parent level"
    )

    def __init__(self, data_version, answer_codes, questionnaire_schema):
        self.data_version = data_version
        self.answer_codes = answer_codes
        self.questionnaire_schema = questionnaire_schema
        self.codes = [answer["code"] for answer in self.answer_codes]
        self.answer_codes_answer_ids = {
            answer["answer_id"] for answer in self.answer_codes
        }
        self.all_answer_ids = list(self.questionnaire_schema.answers_with_context)
        super().__init__(questionnaire_schema)

    def validate(self):
        self.validate_data_version()
        self.validate_duplicate_answer_codes()
        self.validate_missing_answer_id()
        self.validate_missing_answer_codes()
        self.validate_answer_codes_at_option_level()
        self.validate_dynamic_options()
        return self.errors

    def validate_data_version(self):
        if self.data_version != "0.0.3":
            self.add_error(self.INCORRECT_DATA_VERSION_FOR_ANSWER_CODES)

    def validate_duplicate_answer_codes(self):
        duplicates = find_duplicates(self.codes)

        if len(duplicates) > 0:
            self.add_error(self.DUPLICATE_ANSWER_CODE_FOUND, duplicates=duplicates)

    def validate_missing_answer_id(self):
        for answer_code_id in self.answer_codes_answer_ids:
            if answer_code_id not in self.all_answer_ids:
                self.add_error(
                    self.ANSWER_CODE_ANSWER_ID_NOT_FOUND_IN_SCHEMA,
                    answer_id=answer_code_id,
                )

    def validate_missing_answer_codes(self):
        for answer_id in self.all_answer_ids:
            if answer_id not in self.answer_codes_answer_ids:
                self.add_error(self.MISSING_ANSWER_CODE, answer_id=answer_id)

    def validate_dynamic_options(self):
        for answer_id in self.questionnaire_schema.answers_with_context:
            answer = self.questionnaire_schema.answers_with_context[answer_id]

            if "dynamic_options" in answer["answer"]:
                answer_codes_for_options = [
                    answer_code
                    for answer_code in self.answer_codes
                    if answer_code["answer_id"] == answer_id
                ]

                top_level_answer_code_count = sum(
                    "answer_value" not in answer_code
                    for answer_code in answer_codes_for_options
                )
                if top_level_answer_code_count == 0:
                    self.add_error(
                        self.DYNAMIC_ANSWER_OPTION_MUST_HAVE_ANSWER_CODE_SET_AT_TOP_LEVEL,
                        answer_codes_for_options=answer_codes_for_options,
                    )

    def validate_answer_codes_at_option_level(self):
        for answer_id in self.questionnaire_schema.answers_with_context:
            answer = self.questionnaire_schema.answers_with_context[answer_id]

            if "options" in answer["answer"]:
                values = []
                values.extend(option["value"] for option in answer["answer"]["options"])

                answer_codes_for_options = [
                    answer_code
                    for answer_code in self.answer_codes
                    if answer_code["answer_id"] == answer_id
                ]

                self.validate_missing_answer_codes_for_answer_options(
                    answer=answer,
                    answer_id=answer_id,
                    answer_codes_for_options=answer_codes_for_options,
                    values=values,
                )
                self.validate_incorrect_values_in_answer_options(
                    answer_codes_for_options=answer_codes_for_options, values=values
                )

            else:
                for answer_code in self.answer_codes:
                    if answer_code["answer_id"] == answer_id and (
                        "answer_value" in answer_code
                    ):
                        self.add_error(
                            self.ANSWER_VALUE_SET_FOR_ANSWER_WITH_NO_OPTIONS,
                            answer_code=answer_code,
                        )

    def validate_missing_answer_codes_for_answer_options(
        self, answer, answer_id, answer_codes_for_options, values
    ):
        if len(values) != len(answer_codes_for_options) and all(
            "answer_value" in answer_code for answer_code in answer_codes_for_options
        ):
            self.add_error(
                self.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
                answer_options=answer["answer"]["options"],
                answer_codes_for_options=answer_codes_for_options,
            )

        if any(
            "answer_value" not in answer_code
            for answer_code in answer_codes_for_options
        ):
            if len(answer_codes_for_options) == 1:
                if len(values) != 1 and "answer_value" in answer_codes_for_options[0]:
                    self.add_error(
                        self.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
                        answer_options=answer["answer"]["options"],
                        answer_codes_for_options=answer_codes_for_options,
                    )

            elif not self.questionnaire_schema.answers_with_context[answer_id][
                "answer"
            ].get("dynamic_options"):
                # Multiple answer codes are only allowed at the parent level where options are dynamic
                self.add_error(
                    self.MORE_THAN_ONE_ANSWER_CODE_SET_AT_PARENT_LEVEL,
                    answer_options=answer["answer"]["options"],
                    answer_codes_for_options=answer_codes_for_options,
                )

    def validate_incorrect_values_in_answer_options(
        self, answer_codes_for_options, values
    ):
        answer_values = set()
        for answer_code in answer_codes_for_options:
            if answer_code.get("answer_value"):
                answer_values.add(answer_code["answer_value"])

                if answer_code["answer_value"] not in values:
                    self.add_error(
                        self.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
                        answer_value=answer_code["answer_value"],
                        answer_codes_for_options=answer_codes_for_options,
                    )

        if len(answer_values) != len(values) and any(
            "answer_value" in answer_code for answer_code in answer_codes_for_options
        ):
            self.add_error(
                self.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
                answer_codes_for_options=answer_codes_for_options,
            )
