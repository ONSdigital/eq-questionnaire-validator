import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from app.validators.answers.answer_validator import AnswerValidator


class DateAnswerValidator(AnswerValidator):
    INVALID_OFFSET_DATE = "The minimum offset date is greater than the maximum offset date"

    def validate(self):
        super().validate()

        if not self.is_offset_date_valid():
            self.add_error(self.INVALID_OFFSET_DATE)
        return self.errors

    def is_offset_date_valid(self):
        minimum = self.answer.get("minimum")
        maximum = self.answer.get("maximum")
        if not (minimum and maximum):
            return True

        if (
            "value" not in minimum
            or "value" not in maximum
            or isinstance(minimum["value"], dict)
            or isinstance(maximum["value"], dict)
        ):
            return True

        minimum_date = self._get_offset_date(minimum)
        maximum_date = self._get_offset_date(maximum)
        if minimum_date and maximum_date:
            return minimum_date < maximum_date
        return False

    def _get_offset_date(self, answer_min_or_max):
        if answer_min_or_max["value"] == "now":
            value = datetime.utcnow().strftime("%Y-%m-%d")
        else:
            value = answer_min_or_max["value"]

        offset = answer_min_or_max.get("offset_by", {})

        return self.get_relative_date(value, offset)

    @classmethod
    def get_relative_date(cls, date_string, offset_object):
        # Returns a relative date given an offset or period object
        if converted_to_datetime := cls._convert_to_datetime(date_string):
            return converted_to_datetime + relativedelta(
                years=offset_object.get("years", 0),
                months=offset_object.get("months", 0),
                days=offset_object.get("days", 0),
            )
        return None

    @staticmethod
    def _convert_to_datetime(value):
        date_format = "%Y-%m"
        if value and re.match(r"\d{4}-\d{2}-\d{2}", value):
            date_format = "%Y-%m-%d"

        return datetime.strptime(value, date_format) if value else None
