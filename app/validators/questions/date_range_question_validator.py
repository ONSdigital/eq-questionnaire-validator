from app import error_messages
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.questions.question_validator import QuestionValidator


class DateRangeQuestionValidator(QuestionValidator):
    def __init__(self, question):
        super().__init__(question)

        self.period_limits = self.question["period_limits"]

    def validate(self):
        """
        If period_limits object is present in the DateRange question validates that a date range
        does not have a negative period and days can not be used to define limits for yyyy-mm date ranges
        """
        self.validate_range()
        self.validate_period_limits()

    def validate_range(self):
        if "minimum" in self.period_limits and "maximum" in self.period_limits:
            example_date = "2016-05-10"

            # Get minimum and maximum possible dates
            minimum_date = DateAnswerValidator.get_relative_date(
                example_date, self.period_limits["minimum"]
            )
            maximum_date = DateAnswerValidator.get_relative_date(
                example_date, self.period_limits["maximum"]
            )

            if minimum_date > maximum_date:
                self.add_error(error_messages.PERIOD_MIN_GREATER_THAN_MAX)

    def validate_period_limits(self):
        first_answer_type = self.question["answers"][0]["type"]

        has_days_limit = "days" in self.period_limits.get(
            "minimum", []
        ) or "days" in self.period_limits.get("maximum", [])
        has_months_limit = "months" in self.period_limits.get(
            "minimum", []
        ) or "months" in self.period_limits.get("maximum", [])

        if first_answer_type == "MonthYearDate" and has_days_limit:
            self.add_error(error_messages.PERIOD_LIMIT_CANNOT_USE_DAYS)

        if first_answer_type == "YearDate" and (has_days_limit or has_months_limit):
            self.add_error(error_messages.PERIOD_LIMIT_CANNOT_USE_DAYS_MONTHS)
