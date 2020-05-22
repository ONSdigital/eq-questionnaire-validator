from app import error_messages
from app.validators.answers.answer_validator import AnswerValidator


class NumberAnswerValidator(AnswerValidator):
    MAX_NUMBER = 9999999999
    MIN_NUMBER = -999999999
    MAX_DECIMAL_PLACES = 6

    def validate(self):
        super(NumberAnswerValidator, self).validate()

        self.validate_mandatory_has_no_default()
        self.validate_value_in_limits()
        self.validate_decimals()

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
            self.add_error(error_messages.DEFAULT_ON_MANDATORY)

    def validate_value_in_limits(self):
        min_value = self.answer.get("minimum", {}).get("value", 0)
        max_value = self.answer.get("maximum", {}).get("value", 0)

        if isinstance(min_value, int) and min_value < self.MIN_NUMBER:
            self.add_error(
                error_messages.MINIMUM_LESS_THAN_LIMIT,
                value=min_value,
                limit=self.MIN_NUMBER,
            )

        if isinstance(max_value, int) and max_value > self.MAX_NUMBER:
            self.add_error(
                error_messages.MAXIMUM_GREATER_THAN_LIMIT,
                value=max_value,
                limit=self.MAX_NUMBER,
            )

    def validate_decimals(self):
        decimal_places = self.answer.get("decimal_places", 0)
        if decimal_places > self.MAX_DECIMAL_PLACES:
            self.add_error(
                error_messages.DECIMAL_PLACES_TOO_LONG,
                decimal_places=decimal_places,
                limit=self.MAX_DECIMAL_PLACES,
            )
