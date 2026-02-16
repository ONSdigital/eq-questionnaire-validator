"""This module provides the `DateRangeQuestionValidator` class, which is responsible for validating date range questions
in a questionnaire schema.

Classes:
    DateRangeQuestionValidator
"""

from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.questions.question_validator import QuestionValidator


class DateRangeQuestionValidator(QuestionValidator):
    """Validator for date range questions in a questionnaire schema.

    Methods:
        validate
        validate_range
        validate_period_limits
    """

    MIN_GREATER_THAN_MAX = "The minimum period is greater than the maximum period"
    CANNOT_USE_DAYS = "Days can not be used in period_limit for yyyy-mm date range"
    CANNOT_USE_DAYS_MONTHS = "Days/Months can not be used in period_limit for yyyy date range"

    def __init__(self, question):
        super().__init__(question)

        self.period_limits = self.question.get("period_limits", {})

    def validate(self):
        """Validate the date range question.
        If period_limits object is present in the DateRange question validates that a date range
        does not have a negative period and days can not be used to define limits for yyyy-mm date ranges.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()
        self.validate_range()
        self.validate_period_limits()
        return self.errors

    def validate_range(self):
        """Validates that the minimum period is not greater than the maximum period in the period_limits object
        of a DateRange question. It uses an example date to calculate the minimum and maximum possible dates
        based on the provided period limits, and checks if the minimum date is greater than the maximum date.
        """
        if "minimum" in self.period_limits and "maximum" in self.period_limits:
            example_date = "2016-05-10"

            # Get minimum and maximum possible dates
            minimum_date = DateAnswerValidator.get_relative_date(
                example_date,
                self.period_limits["minimum"],
            )
            maximum_date = DateAnswerValidator.get_relative_date(
                example_date,
                self.period_limits["maximum"],
            )

            if (minimum_date and maximum_date) and minimum_date > maximum_date:
                self.add_error(self.MIN_GREATER_THAN_MAX)

    def validate_period_limits(self):
        """If period_limits object is present in the DateRange question, it validates that days can not be used
        to define limits for yyyy-mm and yyyy date ranges.
        """
        first_answer_type = self.answers[0]["type"]

        has_days_limit = "days" in self.period_limits.get(
            "minimum",
            [],
        ) or "days" in self.period_limits.get("maximum", [])
        has_months_limit = "months" in self.period_limits.get(
            "minimum",
            [],
        ) or "months" in self.period_limits.get("maximum", [])

        if first_answer_type == "MonthYearDate" and has_days_limit:
            self.add_error(self.CANNOT_USE_DAYS)

        if first_answer_type == "YearDate" and (has_days_limit or has_months_limit):
            self.add_error(self.CANNOT_USE_DAYS_MONTHS)
