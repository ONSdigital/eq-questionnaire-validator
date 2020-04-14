from functools import cached_property

from app.validation import error_messages
from app.validation.validator import Validator


class AnswerValidator(Validator):
    MAX_NUMBER = 9999999999
    MIN_NUMBER = -999999999
    MAX_DECIMAL_PLACES = 6

    def __init__(self, schema_element, block=None, list_names=None, block_ids=None):
        super().__init__(schema_element)
        self.answer = schema_element
        self.block = block
        self.list_names = list_names
        self.block_ids = block_ids

    @cached_property
    def options(self):
        return self.answer.get("options", [])

    def validate(self):
        self.validate_duplicate_options()
        self.validate_labels_and_values_match()
        self._validate_answer_actions()

        self._validate_routing_on_answer_options()

        if not self.are_decimal_places_valid():
            self.add_error(error_messages.DECIMAL_PLACES_UNDEFINED)

    def validate_duplicate_options(self):
        labels = set()
        values = set()

        for option in self.options:

            # labels can have placeholders, in which case we won't know if they are a duplicate or not
            if isinstance(option["label"], dict):
                continue

            if option["label"] in labels:
                self.add_error(
                    error_messages.DUPLICATE_LABEL_FOUND, label=option["label"]
                )

            if option["value"] in values:
                self.add_error(
                    error_messages.DUPLICATE_VALUE_FOUND, value=option["value"]
                )

            labels.add(option["label"])
            values.add(option["value"])

    def are_decimal_places_valid(self):
        if "calculated" in self.answer:
            return self.answer.get("decimal_places") == 2
        return True

    def validate_labels_and_values_match(self):
        errors = []

        for option in self.options:
            if "text_plural" in option["label"]:
                continue

            if isinstance(option["label"], str):
                label = option["label"]
            else:
                label = option["label"]["text"]

            if label != option["value"]:
                errors.append(
                    f"Found mismatching answer value for label: {label} "
                    f'in answer id: {self.answer["id"]}'
                )
        return errors

    def _validate_answer_actions(self):
        for option in self.options:

            action_params = option.get("action", {}).get("params")
            if not action_params:
                continue

            list_name = action_params.get("list_name")

            if list_name and list_name not in self.list_names:
                self.add_error(error_messages.LIST_NAME_MISSING, list_name=list_name)

            block_id = action_params.get("block_id")

            if block_id and block_id not in self.block_ids:
                self.add_error(error_messages.BLOCK_ID_MISSING, block_id=block_id)

    def has_default_route(self):
        for rule in self.block["routing_rules"]:
            if "goto" not in rule or "when" not in rule["goto"].keys():
                return True
        return False

    def _validate_routing_on_answer_options(self):
        answer_errors = []
        if (
            self.block
            and "routing_rules" in self.block
            and self.block["routing_rules"]
            and self.options
        ):
            option_values = [option["value"] for option in self.options]

            for rule in self.block["routing_rules"]:
                if "goto" in rule and "when" in rule["goto"].keys():
                    when_clause = rule["goto"]["when"]
                    for when in when_clause:
                        if (
                            "id" in when
                            and "value" in when
                            and when["id"] == self.answer["id"]
                            and when["value"] in option_values
                        ):
                            option_values.remove(when["value"])
                else:
                    option_values = []

            has_unrouted_options = option_values and len(option_values) != len(
                self.options
            )

            if self.answer["mandatory"] is False and not self.has_default_route():
                default_route_not_defined = "Default route not defined for optional question [{}]".format(
                    self.answer["id"]
                )
                answer_errors.append(default_route_not_defined)

            if has_unrouted_options:
                unrouted_error_template = (
                    "Routing rule not defined for all answers or default not defined "
                    "for answer [{}] missing options {}"
                )
                unrouted_error = unrouted_error_template.format(
                    self.answer["id"], option_values
                )
                answer_errors.append(unrouted_error)
        return answer_errors

    def validate_numeric_answer_types(self, answer_ranges):
        """
        Validate numeric answer types are valid.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        # Validate referred numeric answer exists (skip further tests for answer if error is returned)
        referred_errors = self._validate_referred_numeric_answer(answer_ranges)

        if referred_errors:
            return

        # Validate numeric answer has a positive range of possible responses
        self._validate_numeric_range(answer_ranges)

        # Validate referred numeric answer decimals
        self._validate_referred_numeric_answer_decimals(answer_ranges)

    def _validate_referred_numeric_answer(self, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        if answer_ranges[self.answer.get("id")]["min"] is None:
            self.add_error(
                error_messages.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
                referenced_id=self.answer["minimum"]["value"]["identifier"],
            )
            return True
        if answer_ranges[self.answer.get("id")]["max"] is None:
            self.add_error(
                error_messages.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
                referenced_id=self.answer["maximum"]["value"]["identifier"],
            )
            return True
        return False

    def _validate_numeric_range(self, answer_ranges):
        max_value = answer_ranges[self.answer.get("id")]["max"]
        min_value = answer_ranges[self.answer.get("id")]["min"]

        if max_value - min_value < 0:
            self.add_error(
                'Invalid range of min = {} and max = {} is possible for answer "{}".'.format(
                    min_value, max_value, self.answer["id"]
                )
            )

    def _validate_referred_numeric_answer_decimals(self, answer_ranges):
        answer_values = answer_ranges[self.answer["id"]]

        if answer_values["min_referred"] is not None:
            referred_values = answer_ranges[answer_values["min_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    error_messages.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["min_referred"],
                )

        if answer_values["max_referred"] is not None:
            referred_values = answer_ranges[answer_values["max_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    error_messages.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["max_referred"],
                )
