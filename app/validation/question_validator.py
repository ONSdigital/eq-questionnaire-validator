from app.validation.answer_validator import AnswerValidator
from app.validation.validator import Validator


class QuestionValidator(Validator):
    question = {}

    def __init__(self, schema_element):
        super().__init__(schema_element)
        self.question = schema_element

    def validate(self):
        self.validate_answers_to_calculate()
        self.validate_date_range()
        self.validate_mutually_exclusive()

    def validate_answers_to_calculate(self):
        """
        Validates that any answer ids within the 'answer_to_group'
        list are existing answers within the question
        """

        if self.question["type"] == "Calculated":
            answer_ids = [answer["id"] for answer in self.question.get("answers")]
            for calculation in self.question.get("calculations"):
                for answer_id in calculation["answers_to_calculate"]:
                    if answer_id not in answer_ids:
                        self.add_error(
                            "Answer id - {} does not exist within this question".format(
                                answer_id
                            )
                        )

    def validate_date_range(self):
        """
        If period_limits object is present in the DateRange question validates that a date range
        does not have a negative period and days can not be used to define limits for yyyy-mm date ranges
        """
        if self.question["type"] == "DateRange" and self.question.get("period_limits"):
            period_limits = self.question["period_limits"]
            if "minimum" in period_limits and "maximum" in period_limits:
                example_date = "2016-05-10"

                # Get minimum and maximum possible dates
                minimum_date = AnswerValidator.get_relative_date(
                    example_date, period_limits["minimum"]
                )
                maximum_date = AnswerValidator.get_relative_date(
                    example_date, period_limits["maximum"]
                )

                if minimum_date > maximum_date:
                    self.add_error(
                        "The minimum period is greater than the maximum period"
                    )

            first_answer_type = self.question["answers"][0]["type"]

            has_days_limit = "days" in period_limits.get(
                "minimum", []
            ) or "days" in period_limits.get("maximum", [])
            has_months_limit = "months" in period_limits.get(
                "minimum", []
            ) or "months" in period_limits.get("maximum", [])

            if first_answer_type == "MonthYearDate" and has_days_limit:
                self.add_error(
                    "Days can not be used in period_limit for yyyy-mm date range"
                )

            if first_answer_type == "YearDate" and (has_days_limit or has_months_limit):
                self.add_error(
                    "Days/Months can not be used in period_limit for yyyy date range"
                )

    def validate_mutually_exclusive(self):
        if self.question["type"] == "MutuallyExclusive":
            answers = self.question["answers"]

            if any(answer["mandatory"] is True for answer in answers):
                self.add_error(
                    "MutuallyExclusive question type cannot contain mandatory answers."
                )

            if answers[-1]["type"] != "Checkbox":
                self.add_error("{} is not of type Checkbox.".format(answers[-1]["id"]))
