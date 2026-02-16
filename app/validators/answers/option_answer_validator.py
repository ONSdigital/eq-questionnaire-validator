"""This module contains the OptionAnswerValidator class, which is responsible for validating answers of type Checkbox,
Radio, and Dropdown.

Classes:
    OptionAnswerValidator
"""

from functools import cached_property

from app.answer_type import AnswerType
from app.validators.answers.answer_validator import AnswerValidator
from app.validators.rules.rule_validator import RulesValidator

MIN_OPTIONS_BY_ANSWER_TYPE = {
    AnswerType.CHECKBOX: 1,
    AnswerType.RADIO: 2,
    AnswerType.DROPDOWN: 2,
}


class OptionAnswerValidator(AnswerValidator):
    """Validator for answers of type Checkbox, Radio, and Dropdown.

    Attributes:
        schema_element (Mapping): The answer to be validated.
        questionnaire_schema (QuestionnaireSchema): The questionnaire schema to validate against.

    Methods:
        validate
        validate_min_options
        validate_duplicate_options
        validate_default_exists_in_options
        validate_dynamic_options
        _validate_dynamic_options_value_rules
        _validate_dynamic_options_answer_source
    """

    DUPLICATE_LABEL = "Duplicate label found"
    DUPLICATE_VALUE = "Duplicate value found"
    LIST_NAME_MISSING = "List name defined in action params does not exist"
    BLOCK_ID_MISSING = "Block id defined in action params does not exist"
    ANSWER_DEFAULT_MISSING = "Couldn't find matching value for answer default"
    NOT_ENOUGH_ANSWER_OPTIONS = (
        "Not enough options. "
        "{answer_type} requires at least {required_num_options} answer option(s) but got {actual_num_options}"
    )
    OPTIONS_DEFINED_BUT_EMPTY = "Answer options defined, but empty"
    DYNAMIC_OPTIONS_REFERENCES_NON_CHECKBOX_ANSWER = "Dynamic options references non Checkbox answer"
    DYNAMIC_OPTIONS_SOURCE_IDENTIFIER_AND_OPTION_LABEL_FROM_VALUE_MISMATCH = (
        "Dynamic options source identifier and option label from value answer_id do not match"
    )

    def __init__(self, schema_element, questionnaire_schema):
        super().__init__(schema_element, questionnaire_schema)

        self.questionnaire_schema = questionnaire_schema
        self.list_names = self.questionnaire_schema.list_names
        self.block_ids = self.questionnaire_schema.block_ids

    def validate(self):
        """Validates the answer by performing several checks on the options and dynamic options.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()
        self.validate_min_options()
        self.validate_duplicate_options()
        self.validate_default_exists_in_options()
        self.validate_dynamic_options()
        return self.errors

    @cached_property
    def options(self):
        """Simple getter for the options defined on the answer, with caching to avoid repeated dictionary lookups.

        Returns:
            A list of options for the answer, or an empty list if no options are defined.
        """
        return self.answer.get("options", [])

    @cached_property
    def dynamic_options(self):
        """Simple getter for the dynamic options defined on the answer, with caching to avoid repeated dictionary
        lookups.

        Returns:
            A dictionary containing the dynamic options for the answer, or an empty dictionary if no dynamic options
        """
        return self.answer.get("dynamic_options", {})

    def validate_min_options(self):
        """Validates that the answer has the minimum number of options required based on its type, and that if
        dynamic options are defined, they are not empty.
        """
        options_len = len(self.options)
        min_options = MIN_OPTIONS_BY_ANSWER_TYPE[self.answer_type]

        if self.dynamic_options:
            if "options" in self.answer and options_len == 0:
                self.add_error(self.OPTIONS_DEFINED_BUT_EMPTY)
        elif options_len < min_options:
            self.add_error(
                self.NOT_ENOUGH_ANSWER_OPTIONS.format(
                    answer_type=self.answer_type.value,
                    required_num_options=min_options,
                    actual_num_options=options_len,
                ),
            )

    def validate_duplicate_options(self):
        """Validates that there are no duplicate labels or values in the options defined on the answer. If an option
        label is a dictionary, it is assumed to be a placeholder and is not checked for duplicates.
        """
        labels = set()
        values = set()

        for option in self.options:
            # labels can have placeholders, in which case we won't know if they are a duplicate or not
            if isinstance(option["label"], dict):
                continue

            if option["label"] in labels:
                self.add_error(self.DUPLICATE_LABEL, label=option["label"])

            if option["value"] in values:
                self.add_error(self.DUPLICATE_VALUE, value=option["value"])

            labels.add(option["label"])
            values.add(option["value"])

    def validate_default_exists_in_options(self):
        """Validates that if a default value is defined for the answer, it exists in the options defined for
        the answer.
        """
        default_value = self.answer.get("default")
        if default_value and default_value not in [option["value"] for option in self.options]:
            self.add_error(self.ANSWER_DEFAULT_MISSING, default_value=default_value)

    def validate_dynamic_options(self):
        """Validates the dynamic options defined on the answer, if they exist, by checking the validity of the
        answer.
        """
        if not self.dynamic_options:
            return

        self._validate_dynamic_options_answer_source()
        self._validate_dynamic_options_value_rules()

    def _validate_dynamic_options_value_rules(self):
        """Validates the rules defined in the dynamic options for the answer, if they exist, by using the
        RulesValidator.
        """
        for key_to_validate, allow_self_reference in [
            ("values", False),
            ("transform", True),
        ]:
            validator = RulesValidator(
                self.dynamic_options[key_to_validate],
                self.answer_id,
                self.questionnaire_schema,
                allow_self_reference=allow_self_reference,
            )
            self.errors += validator.validate()

    def _validate_dynamic_options_answer_source(self):
        """Validates the answer source defined in the dynamic options for the answer, if it exists, by checking that if
        the source is "answers", the identifier references an answer of type Checkbox, and that if the transform
        option-label-from-value is used, the identifier in the source matches the identifier in the transform.
        """
        if "source" not in self.dynamic_options["values"]:
            return

        value_source = self.dynamic_options["values"]
        transform = self.dynamic_options["transform"]

        if value_source["source"] == "answers":
            if self.questionnaire_schema.get_answer_type(value_source["identifier"]) != AnswerType.CHECKBOX:
                self.add_error(
                    self.DYNAMIC_OPTIONS_REFERENCES_NON_CHECKBOX_ANSWER,
                    value_source=value_source,
                )

            if (
                "option-label-from-value" in transform
                and transform["option-label-from-value"][1] != value_source["identifier"]
            ):
                self.add_error(
                    self.DYNAMIC_OPTIONS_SOURCE_IDENTIFIER_AND_OPTION_LABEL_FROM_VALUE_MISMATCH,
                    source_identifier=value_source["identifier"],
                    transform_identifier=transform["option-label-from-value"][1],
                )
