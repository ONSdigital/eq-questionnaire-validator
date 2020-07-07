from functools import cached_property

from app.validators.answers import AnswerValidator


class OptionAnswerValidator(AnswerValidator):
    DUPLICATE_LABEL = "Duplicate label found"
    DUPLICATE_VALUE = "Duplicate value found"
    ANSWER_LABEL_VALUE_MISMATCH = "Found mismatching answer value for label"
    LIST_NAME_MISSING = "List name defined in action params does not exist"
    BLOCK_ID_MISSING = "Block id defined in action params does not exist"
    ANSWER_DEFAULT_MISSING = "Couldn't find matching value for answer default"

    def __init__(self, schema_element, questionnaire_schema=None):
        super().__init__(schema_element)
        if questionnaire_schema:
            self.list_names = questionnaire_schema.list_names
            self.block_ids = questionnaire_schema.block_ids

    def validate(self):
        super().validate()
        self.validate_duplicate_options()
        self.validate_labels_and_values_match()
        self.validate_answer_actions()
        self.validate_default_exists_in_options()
        return self.errors

    @cached_property
    def options(self):
        return self.answer.get("options", [])

    def validate_duplicate_options(self):
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

    def validate_default_exists_in_options(self):
        default_value = self.answer.get("default")
        if default_value and default_value not in [
            option["value"] for option in self.options
        ]:
            self.add_error(
                self.ANSWER_DEFAULT_MISSING, default=default_value, options=self.options
            )
