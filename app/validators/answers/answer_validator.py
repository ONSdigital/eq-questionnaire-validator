from functools import cached_property

from app.validators.validator import Validator


class AnswerValidator(Validator):
    ANSWER_RANGE_INVALID = "Invalid range of min and max is possible for answer"
    DECIMAL_PLACES_UNDEFINED = "'decimal_places' must be defined and set to 2"
    DUPLICATE_LABEL_FOUND = "Duplicate label found"
    DUPLICATE_VALUE_FOUND = "Duplicate value found"
    ANSWER_LABEL_VALUE_MISMATCH = "Found mismatching answer value for label"
    LIST_NAME_MISSING = "List name defined in action params does not exist"
    BLOCK_ID_MISSING = "Block id defined in action params does not exist"
    MINIMUM_CANNOT_BE_SET_WITH_ANSWER = (
        "The referenced answer cannot be used to set the minimum of answer"
    )
    MAXIMUM_CANNOT_BE_SET_WITH_ANSWER = (
        "The referenced answer cannot be used to set the maximum of answer"
    )
    GREATER_DECIMALS_ON_ANSWER_REFERENCE = (
        "The referenced answer has a greater number of decimal places than answer"
    )

    def __init__(self, schema_element, questionnaire_schema=None):
        super().__init__(schema_element)
        self.answer = schema_element
        if questionnaire_schema:
            self.list_names = questionnaire_schema.list_names
            self.block_ids = questionnaire_schema.block_ids
        self.context["answer_id"] = self.answer["id"]

    @cached_property
    def options(self):
        return self.answer.get("options", [])

    def validate(self):
        self.validate_duplicate_options()
        self.validate_labels_and_values_match()
        self.validate_decimal_places()
        self.validate_answer_actions()
        return self.errors

    def validate_duplicate_options(self):
        labels = set()
        values = set()

        for option in self.options:

            # labels can have placeholders, in which case we won't know if they are a duplicate or not
            if isinstance(option["label"], dict):
                continue

            if option["label"] in labels:
                self.add_error(self.DUPLICATE_LABEL_FOUND, label=option["label"])

            if option["value"] in values:
                self.add_error(self.DUPLICATE_VALUE_FOUND, value=option["value"])

            labels.add(option["label"])
            values.add(option["value"])

    def are_decimal_places_valid(self):
        if "calculated" in self.answer:
            return self.answer.get("decimal_places") == 2
        return True

    def validate_decimal_places(self):
        if not self.are_decimal_places_valid():
            self.add_error(self.DECIMAL_PLACES_UNDEFINED)

    def validate_labels_and_values_match(self):
        for option in self.options:
            if "text_plural" in option["label"]:
                continue

            if isinstance(option["label"], str):
                label = option["label"]
            else:
                label = option["label"]["text"]

            if label != option["value"]:
                self.add_error(
                    self.ANSWER_LABEL_VALUE_MISMATCH, label=label, value=option["value"]
                )

    def validate_answer_actions(self):
        for option in self.options:

            action_params = option.get("action", {}).get("params")
            if not action_params:
                continue

            list_name = action_params.get("list_name")

            if list_name and list_name not in self.list_names:
                self.add_error(self.LIST_NAME_MISSING, list_name=list_name)

            block_id = action_params.get("block_id")

            if block_id and block_id not in self.block_ids:
                self.add_error(self.BLOCK_ID_MISSING, block_id=block_id)
