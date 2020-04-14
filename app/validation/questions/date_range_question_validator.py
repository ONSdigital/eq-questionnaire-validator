from app.validation.answers.date_answer_validator import DateAnswerValidator
from app.validation.questions.question_validator import QuestionValidator


class DateRangeQuestionValidator(QuestionValidator):
    def validate(self):
        """
        If period_limits object is present in the DateRange question validates that a date range
        does not have a negative period and days can not be used to define limits for yyyy-mm date ranges
        """
        period_limits = self.question["period_limits"]
        if "minimum" in period_limits and "maximum" in period_limits:
            example_date = "2016-05-10"

            # Get minimum and maximum possible dates
            minimum_date = DateAnswerValidator.get_relative_date(
                example_date, period_limits["minimum"]
            )
            maximum_date = DateAnswerValidator.get_relative_date(
                example_date, period_limits["maximum"]
            )

            if minimum_date > maximum_date:
                self.add_error("The minimum period is greater than the maximum period")

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
