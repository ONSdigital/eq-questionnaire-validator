"""This module contains the DateAnswerValidator class which validates date answers in a questionnaire.

Classes:
    DateAnswerValidator
"""

import re
from datetime import datetime

from dateutil.relativedelta import relativedelta

from app.validators.answers.answer_validator import AnswerValidator


class DateAnswerValidator(AnswerValidator):
    """Validates date answers in a questionnaire.

    Methods:
        validate
        is_offset_date_valid
        _get_offset_date
        get_relative_date
        _convert_to_datetime
    """

    INVALID_OFFSET_DATE = "The minimum offset date is greater than the maximum offset date"

    def validate(self):
        """Validates the date answer by invoking the parent validate method and then checking if the offset dates are
        valid.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()

        if not self.is_offset_date_valid():
            self.add_error(self.INVALID_OFFSET_DATE)
        return self.errors

    def is_offset_date_valid(self):
        """Checks if the minimum offset date is less than the maximum offset date if both are present and have valid
        values.

        Returns:
            bool: True if the minimum offset date is less than the maximum offset date, or if either is missing or has
            an invalid value. False if both are present and have valid values but the minimum offset date is
            greater than or equal to the maximum offset date.
        """
        if "minimum" in self.answer and "maximum" in self.answer:
            if (
                "value" in self.answer["minimum"]
                and "value" in self.answer["maximum"]
                and not isinstance(self.answer["minimum"]["value"], dict)
                and not isinstance(self.answer["maximum"]["value"], dict)
            ):
                minimum_date = self._get_offset_date(self.answer["minimum"])
                maximum_date = self._get_offset_date(self.answer["maximum"])
                return minimum_date < maximum_date if minimum_date and maximum_date else False
        return True

    def _get_offset_date(self, answer_min_or_max):
        """Returns the offset date for a given minimum or maximum answer object.

        Args:
            answer_min_or_max (dict): The minimum or maximum answer object containing the value and offset information.

        Returns:
            Invocation of get_relative_date.
        """
        if answer_min_or_max["value"] == "now":
            value = datetime.utcnow().strftime("%Y-%m-%d")
        else:
            value = answer_min_or_max["value"]

        offset = answer_min_or_max.get("offset_by", {})

        return self.get_relative_date(value, offset)

    @classmethod
    def get_relative_date(cls, date_string, offset_object):
        """Class method that returns a relative date given a date string and an offset object.

        Args:
            date_string (str): The date string to which the offset will be applied. It can
            be in the format "YYYY-MM-DD" or "YYYY-MM".
            offset_object (dict): A dictionary containing the offset values for years, months, and days.

        Returns:
            A datetime object representing the relative date obtained by applying the offset to the given date string,
            or None if the date string cannot be converted to a datetime object.
        """
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
        """Converts a date string to a datetime object. The date string can be in the format "YYYY-MM-DD" or YYYY-MM".

        Args:
            value (str): The date string to convert.

        Returns:
            A datetime object representing the given date string, or None if the value is empty or cannot be converted
            to a datetime object.
        """
        date_format = "%Y-%m"
        if value and re.match(r"\d{4}-\d{2}-\d{2}", value):
            date_format = "%Y-%m-%d"

        return datetime.strptime(value, date_format) if value else None
