import re
from datetime import datetime
from functools import cached_property
from urllib.parse import urlparse

from dateutil.relativedelta import relativedelta


MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


class AnswerValidator:
    schema_element = {}

    def __init__(self, schema_element, block, list_names, block_ids):
        self.schema_element = schema_element
        self.block = block
        self.list_names = list_names
        self.block_ids = block_ids

    @cached_property
    def options(self):
        return self.schema_element.get("options", [])

    def validate(self):
        errors = []
        errors.extend(self._validate_duplicate_options())
        errors.extend(self._validate_totaliser_defines_decimal_places())
        errors.extend(self._validate_answer_actions())
        errors.extend(self._ensure_answer_labels_and_values_match())

        errors.extend(self._validate_routing_on_answer_options())

        if self.schema_element["type"] == "Date" and not self.is_offset_date_valid():
            errors.append(
                "The minimum offset date is greater than the maximum offset date"
            )

        if (
            self.schema_element["type"] == "TextField"
            and "suggestions_url" in self.schema_element
        ):
            if not self.is_suggestion_url_valid():
                errors.append(
                    f'Suggestions url used for TextField `{self.schema_element["id"]}` is invalid'
                )
        return errors

    def _validate_duplicate_options(self):
        errors = []

        labels = set()
        values = set()

        for option in self.options:

            # labels can have placeholders in, in which case we won't know if they are a duplicate or not
            if isinstance(option["label"], dict):
                continue

            if option["label"] in labels:
                errors.append("Duplicate label found - {}".format(option["label"]))

            if option["value"] in values:
                errors.append("Duplicate value found - {}".format(option["value"]))

            labels.add(option["label"])
            values.add(option["value"])

        return errors

    def _validate_totaliser_defines_decimal_places(self):
        errors = []

        if "calculated" in self.schema_element and (
            "decimal_places" not in self.schema_element
            or self.schema_element["decimal_places"] != 2
        ):
            errors.append(
                "'decimal_places' must be defined and set to 2 for the answer_id - {}".format(
                    self.schema_element["id"]
                )
            )

        return errors

    def _validate_answer_actions(self):
        errors = []
        for option in self.options:

            action_params = option.get("action", {}).get("params")
            if not action_params:
                continue

            list_name = action_params.get("list_name")

            if list_name and list_name not in self.list_names:
                errors.append(
                    f'List name `{list_name}` defined in action params for answer `{self.schema_element["id"]}` does not exist'
                )

            block_id = action_params.get("block_id")
            if block_id and block_id not in self.block_ids:
                errors.append(
                    f'The block_id `{block_id}` defined in action params for answer `{self.schema_element["id"]}` does not exist'
                )

        return errors

    def _ensure_answer_labels_and_values_match(self):
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
                    f'in answer id: {self.schema_element["id"]}'
                )
        return errors

    def is_offset_date_valid(self):
        if "minimum" in self.schema_element and "maximum" in self.schema_element:
            if (
                "value" in self.schema_element["minimum"]
                and "value" in self.schema_element["maximum"]
                and not isinstance(self.schema_element["minimum"]["value"], dict)
                and not isinstance(self.schema_element["maximum"]["value"], dict)
            ):
                minimum_date = self._get_offset_date(self.schema_element["minimum"])
                maximum_date = self._get_offset_date(self.schema_element["maximum"])

                return minimum_date < maximum_date
        return True

    def _validate_routing_on_answer_options(self):
        answer_errors = []
        if (
            "routing_rules" in self.block
            and self.block["routing_rules"]
            and self.options
        ):
            option_values = [option["value"] for option in self.options]
            has_default_route = False

            for rule in self.block["routing_rules"]:
                if "goto" in rule and "when" in rule["goto"].keys():
                    when_clause = rule["goto"]["when"]
                    for when in when_clause:
                        if (
                            "id" in when
                            and "value" in when
                            and when["id"] == self.schema_element["id"]
                            and when["value"] in option_values
                        ):
                            option_values.remove(when["value"])
                else:
                    option_values = []
                    has_default_route = True

            has_unrouted_options = option_values and len(option_values) != len(
                self.options
            )

            if self.schema_element["mandatory"] is False and not has_default_route:
                default_route_not_defined = "Default route not defined for optional question [{}]".format(
                    self.schema_element["id"]
                )
                answer_errors.append(default_route_not_defined)

            if has_unrouted_options:
                unrouted_error_template = (
                    "Routing rule not defined for all answers or default not defined "
                    "for answer [{}] missing options {}"
                )
                unrouted_error = unrouted_error_template.format(
                    self.schema_element["id"], option_values
                )
                answer_errors.append(unrouted_error)
        return answer_errors

    def validate_numeric_answer_types(self, answer_ranges):
        """
        Validate numeric answer types are valid.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []

        # Validate referred numeric answer exists (skip further tests for answer if error is returned)
        referred_errors = self._validate_referred_numeric_answer(answer_ranges)
        errors.extend(referred_errors)
        if referred_errors:
            return errors

        # Validate numeric answer has a positive range of possible responses
        errors.extend(self._validate_numeric_range(answer_ranges))

        # Validate numeric answer value within system limits
        errors.extend(self._validate_numeric_answer_value())

        # Validate numeric answer decimal places within system limits
        errors.extend(self._validate_numeric_answer_decimals())

        # Validate referred numeric answer decimals
        errors.extend(self._validate_referred_numeric_answer_decimals(answer_ranges))

        # Validate default is only used with non mandatory answers
        errors.extend(self._validate_numeric_default())

        return errors

    def _validate_referred_numeric_answer(self, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        errors = []
        if answer_ranges[self.schema_element.get("id")]["min"] is None:
            error_message = 'The referenced answer "{}" can not be used to set the minimum of answer "{}"'.format(
                self.schema_element["minimum"]["value"]["identifier"],
                self.schema_element["id"],
            )
            errors.append(error_message)
        if answer_ranges[self.schema_element.get("id")]["max"] is None:
            error_message = 'The referenced answer "{}" can not be used to set the maximum of answer "{}"'.format(
                self.schema_element["maximum"]["value"]["identifier"],
                self.schema_element["id"],
            )
            errors.append(error_message)

        return errors

    def _validate_numeric_range(self, answer_ranges):
        errors = []
        max_value = answer_ranges[self.schema_element.get("id")]["max"]
        min_value = answer_ranges[self.schema_element.get("id")]["min"]

        if max_value - min_value < 0:
            error_message = 'Invalid range of min = {} and max = {} is possible for answer "{}".'.format(
                min_value, max_value, self.schema_element["id"]
            )
            errors.append(error_message)

        return errors

    def _validate_numeric_answer_value(self):
        errors = []

        min_value = self.schema_element.get("minimum", {}).get("value", 0)
        max_value = self.schema_element.get("maximum", {}).get("value", 0)

        if isinstance(min_value, int) and min_value < MIN_NUMBER:
            error_message = 'Minimum value {} for answer "{}" is less than system limit of {}'.format(
                min_value, self.schema_element["id"], MIN_NUMBER
            )
            errors.append(error_message)

        if isinstance(max_value, int) and max_value > MAX_NUMBER:
            error_message = 'Maximum value {} for answer "{}" is greater than system limit of {}'.format(
                max_value, self.schema_element["id"], MAX_NUMBER
            )
            errors.append(error_message)

        return errors

    def _validate_numeric_answer_decimals(self):
        errors = []
        if self.schema_element.get("decimal_places", 0) > MAX_DECIMAL_PLACES:
            error_message = 'Number of decimal places {} for answer "{}" is greater than system limit of {}'.format(
                self.schema_element["decimal_places"],
                self.schema_element["id"],
                MAX_DECIMAL_PLACES,
            )
            errors.append(error_message)

        return errors

    def _validate_referred_numeric_answer_decimals(self, answer_ranges):
        errors = []
        answer_values = answer_ranges[self.schema_element["id"]]

        if answer_values["min_referred"] is not None:
            referred_values = answer_ranges[answer_values["min_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                error_message = 'The referenced answer "{}" has a greater number of decimal places than answer "{}"'.format(
                    answer_values["min_referred"], self.schema_element["id"]
                )
                errors.append(error_message)

        if answer_values["max_referred"] is not None:
            referred_values = answer_ranges[answer_values["max_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                error_message = 'The referenced answer "{}" has a greater number of decimal places than answer "{}"'.format(
                    answer_values["max_referred"], self.schema_element["id"]
                )
                errors.append(error_message)

        return errors

    def _validate_numeric_default(self):
        if (
            self.schema_element.get("mandatory")
            and self.schema_element.get("default") is not None
        ):
            return [
                "Default is being used with a mandatory answer: {}".format(
                    self.schema_element["id"]
                )
            ]

        return []

    def _get_offset_date(self, answer_min_or_max):
        if answer_min_or_max["value"] == "now":
            value = datetime.utcnow().strftime("%Y-%m-%d")
        else:
            value = answer_min_or_max["value"]

        offset = answer_min_or_max.get("offset_by", {})

        return self.get_relative_date(value, offset)

    def get_numeric_range_values(self, answer_ranges):
        min_value = self.schema_element.get("minimum", {}).get("value", {})
        max_value = self.schema_element.get("maximum", {}).get("value", {})
        min_referred = (
            min_value.get("identifier") if isinstance(min_value, dict) else None
        )
        max_referred = (
            max_value.get("identifier") if isinstance(max_value, dict) else None
        )

        exclusive = self.schema_element.get("exclusive", False)
        decimal_places = self.schema_element.get("decimal_places", 0)

        return {
            "min": self._get_answer_minimum(
                min_value, decimal_places, exclusive, answer_ranges
            ),
            "max": self._get_answer_maximum(
                max_value, decimal_places, exclusive, answer_ranges
            ),
            "decimal_places": decimal_places,
            "min_referred": min_referred,
            "max_referred": max_referred,
            "default": self.schema_element.get("default"),
        }

    def _get_answer_minimum(
        self, defined_minimum, decimal_places, exclusive, answer_ranges
    ):
        minimum_value = self._get_defined_numeric_value(
            defined_minimum, 0, answer_ranges
        )
        if exclusive:
            return minimum_value + (1 / 10 ** decimal_places)
        return minimum_value

    def _get_answer_maximum(
        self, defined_maximum, decimal_places, exclusive, answer_ranges
    ):
        maximum_value = self._get_defined_numeric_value(
            defined_maximum, MAX_NUMBER, answer_ranges
        )
        if exclusive:
            return maximum_value - (1 / 10 ** decimal_places)
        return maximum_value

    @staticmethod
    def get_relative_date(date_string, offset_object):
        # Returns a relative date given an offset or period object
        return AnswerValidator._convert_to_datetime(date_string) + relativedelta(
            years=offset_object.get("years", 0),
            months=offset_object.get("months", 0),
            days=offset_object.get("days", 0),
        )

    @staticmethod
    def _get_defined_numeric_value(defined_value, system_default, answer_ranges):
        if not isinstance(defined_value, dict):
            return defined_value
        if "source" in defined_value and defined_value["source"] == "answers":
            referred_answer = answer_ranges.get(defined_value["identifier"])
            if referred_answer is None:
                # Referred answer is not valid (picked up by _validate_referred_numeric_answer)
                return None
            if referred_answer.get("default") is not None:
                return system_default
        return system_default

    @staticmethod
    def _convert_to_datetime(value):
        date_format = "%Y-%m"
        if value and re.match(r"\d{4}-\d{2}-\d{2}", value):
            date_format = "%Y-%m-%d"

        return datetime.strptime(value, date_format) if value else None

    def is_suggestion_url_valid(self):
        parsed_result = urlparse(self.schema_element["suggestions_url"])

        if parsed_result.scheme and parsed_result.netloc:
            return True
        return re.match(r"^[A-Za-z0-9_.\-/~]+$", parsed_result.path) is not None
