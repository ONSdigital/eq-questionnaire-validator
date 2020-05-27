from app.validators.answers.answer_validator import AnswerValidator


class NumberAnswerValidator(AnswerValidator):
    MAX_NUMBER = 9999999999
    MIN_NUMBER = -999999999
    MAX_DECIMAL_PLACES = 6

    DEFAULT_ON_MANDATORY = "Default is being used with a mandatory answer"
    MINIMUM_LESS_THAN_LIMIT = "Minimum value is less than system limit"
    MAXIMUM_GREATER_THAN_LIMIT = "Maximum value is greater than system limit"
    DECIMAL_PLACES_TOO_LONG = "Number of decimal places is greater than system limit"

    def validate(self):
        super().validate()

        self.validate_mandatory_has_no_default()
        self.validate_value_in_limits()
        self.validate_decimals()
        return self.errors

    def get_numeric_range_values(self, answer_ranges):
        min_value = self.answer.get("minimum", {}).get("value", {})
        max_value = self.answer.get("maximum", {}).get("value", {})
        min_referred = (
            min_value.get("identifier") if isinstance(min_value, dict) else None
        )
        max_referred = (
            max_value.get("identifier") if isinstance(max_value, dict) else None
        )

        exclusive = self.answer.get("exclusive", False)
        decimal_places = self.answer.get("decimal_places", 0)

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
            "default": self.answer.get("default"),
        }

    def _get_answer_minimum(
        self, defined_minimum, decimal_places, exclusive, answer_ranges
    ):
        minimum_value = self._get_numeric_value(defined_minimum, 0, answer_ranges)
        if exclusive:
            return minimum_value + (1 / 10 ** decimal_places)
        return minimum_value

    def _get_answer_maximum(
        self, defined_maximum, decimal_places, exclusive, answer_ranges
    ):
        maximum_value = self._get_numeric_value(
            defined_maximum, self.MAX_NUMBER, answer_ranges
        )
        if exclusive:
            return maximum_value - (1 / 10 ** decimal_places)
        return maximum_value

    @staticmethod
    def _get_numeric_value(defined_value, system_default, answer_ranges):
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

    def validate_mandatory_has_no_default(self):
        if self.answer.get("mandatory") and self.answer.get("default") is not None:
            self.add_error(self.DEFAULT_ON_MANDATORY)

    def validate_value_in_limits(self):
        min_value = self.answer.get("minimum", {}).get("value", 0)
        max_value = self.answer.get("maximum", {}).get("value", 0)

        if isinstance(min_value, int) and min_value < self.MIN_NUMBER:
            self.add_error(
                self.MINIMUM_LESS_THAN_LIMIT, value=min_value, limit=self.MIN_NUMBER
            )

        if isinstance(max_value, int) and max_value > self.MAX_NUMBER:
            self.add_error(
                self.MAXIMUM_GREATER_THAN_LIMIT, value=max_value, limit=self.MAX_NUMBER
            )

    def validate_decimals(self):
        decimal_places = self.answer.get("decimal_places", 0)
        if decimal_places > self.MAX_DECIMAL_PLACES:
            self.add_error(
                self.DECIMAL_PLACES_TOO_LONG,
                decimal_places=decimal_places,
                limit=self.MAX_DECIMAL_PLACES,
            )

    def validate_numeric_answer_types(self, answer_ranges):
        """
        Validate numeric answer types are valid.
        """
        # Validate referred numeric answer exists (skip further tests for answer if error is returned)
        referred_errors = self.validate_referred_numeric_answer(answer_ranges)

        if referred_errors:
            return

        # Validate numeric answer has a positive range of possible responses
        self.validate_numeric_range(answer_ranges)

        # Validate referred numeric answer decimals
        self.validate_referred_numeric_answer_decimals(answer_ranges)

    def validate_referred_numeric_answer(self, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        errors_found = False
        if answer_ranges[self.answer.get("id")]["min"] is None:
            self.add_error(
                self.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
                referenced_id=self.answer["minimum"]["value"]["identifier"],
            )
            errors_found = True
        if answer_ranges[self.answer.get("id")]["max"] is None:
            self.add_error(
                self.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
                referenced_id=self.answer["maximum"]["value"]["identifier"],
            )
            errors_found = True
        return errors_found

    def validate_numeric_range(self, answer_ranges):
        max_value = answer_ranges[self.answer.get("id")]["max"]
        min_value = answer_ranges[self.answer.get("id")]["min"]

        if max_value - min_value < 0:
            self.add_error(
                self.ANSWER_RANGE_INVALID,
                min=min_value,
                max=max_value,
                answer_id=self.answer["id"],
            )

    def validate_referred_numeric_answer_decimals(self, answer_ranges):
        answer_values = answer_ranges[self.answer["id"]]

        if answer_values["min_referred"] is not None:
            referred_values = answer_ranges[answer_values["min_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    self.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["min_referred"],
                )

        if answer_values["max_referred"] is not None:
            referred_values = answer_ranges[answer_values["max_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    self.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["max_referred"],
                )
