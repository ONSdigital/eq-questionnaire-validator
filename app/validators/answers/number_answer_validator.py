from app.validators.answers.answer_validator import AnswerValidator

MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


class NumberAnswerValidator(AnswerValidator):
    DEFAULT_ON_MANDATORY = "Default answer is being used with a mandatory answer"
    MINIMUM_LESS_THAN_LIMIT = "Minimum value is less than system limit"
    MAXIMUM_GREATER_THAN_LIMIT = "Maximum value is greater than system limit"
    DECIMAL_PLACES_TOO_LONG = "Number of decimal places is greater than system limit"
    DECIMAL_PLACES_UNDEFINED = "'decimal_places' must be defined and set to 2"
    ANSWER_RANGE_INVALID = "Invalid range of min and max is possible for answer"
    MINIMUM_CANNOT_BE_SET_WITH_ANSWER = (
        "The referenced answer cannot be used to set the minimum of answer"
    )
    MAXIMUM_CANNOT_BE_SET_WITH_ANSWER = (
        "The referenced answer cannot be used to set the maximum of answer"
    )
    GREATER_DECIMALS_ON_ANSWER_REFERENCE = (
        "The referenced answer has a greater number of decimal places than answer"
    )

    def __init__(self, schema_element, questionnaire_schema):
        super().__init__(schema_element, questionnaire_schema)
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        super().validate()

        self.validate_decimal_places()
        self.validate_mandatory_has_no_default()
        self.validate_value_in_limits()
        self.validate_decimals()

        if self.questionnaire_schema:
            # Validate referred numeric answer exists (skip further tests for answer if error is returned)
            referred_errors = self.validate_referred_numeric_answer(
                self.questionnaire_schema.numeric_answer_ranges
            )

            if referred_errors:
                return

            # Validate numeric answer has a positive range of possible responses
            self.validate_numeric_range(self.questionnaire_schema.numeric_answer_ranges)

            # Validate referred numeric answer decimals
            self.validate_referred_numeric_answer_decimals(
                self.questionnaire_schema.numeric_answer_ranges
            )

        return self.errors

    def validate_mandatory_has_no_default(self):
        if self.answer.get("mandatory") and self.answer.get("default") is not None:
            self.add_error(self.DEFAULT_ON_MANDATORY)

    def validate_value_in_limits(self):
        min_value = self.answer.get("minimum", {}).get("value", 0)
        max_value = self.answer.get("maximum", {}).get("value", 0)

        if isinstance(min_value, int) and min_value < MIN_NUMBER:
            self.add_error(
                self.MINIMUM_LESS_THAN_LIMIT, value=min_value, limit=MIN_NUMBER
            )

        if isinstance(max_value, int) and max_value > MAX_NUMBER:
            self.add_error(
                self.MAXIMUM_GREATER_THAN_LIMIT, value=max_value, limit=MAX_NUMBER
            )

    def are_decimal_places_valid(self):
        if "calculated" in self.answer:
            return self.answer.get("decimal_places") == 2
        return True

    def validate_decimal_places(self):
        if not self.are_decimal_places_valid():
            self.add_error(self.DECIMAL_PLACES_UNDEFINED)

    def validate_decimals(self):
        decimal_places = self.answer.get("decimal_places", 0)
        if decimal_places > MAX_DECIMAL_PLACES:
            self.add_error(
                self.DECIMAL_PLACES_TOO_LONG,
                decimal_places=decimal_places,
                limit=MAX_DECIMAL_PLACES,
            )

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

        if (
            answer_values["min_referred"] is not None
            and answer_values["min_referred"] in answer_ranges
        ):
            referred_values = answer_ranges[answer_values["min_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    self.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["min_referred"],
                )

        if (
            answer_values["max_referred"] is not None
            and answer_values["max_referred"] in answer_ranges
        ):
            referred_values = answer_ranges[answer_values["max_referred"]]
            if answer_values["decimal_places"] < referred_values["decimal_places"]:
                self.add_error(
                    self.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
                    referenced_id=answer_values["max_referred"],
                )
