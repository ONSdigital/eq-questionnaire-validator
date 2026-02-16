"""Defines the AnswerType and AnswerOptionType enums that are used in validators to specify the types of answers that
can be validated.

Classes:
    AnswerType
    AnswerOptionType
"""

from enum import Enum


class AnswerType(Enum):
    """Defines the types of answers that can be used in validators and reflect the answer types in the schema."""

    ADDRESS = "Address"
    CHECKBOX = "Checkbox"
    CURRENCY = "Currency"
    DATE = "Date"
    DROPDOWN = "Dropdown"
    DURATION = "Duration"
    MOBILE_NUMBER = "MobileNumber"
    MONTH_YEAR_DATE = "MonthYearDate"
    NUMBER = "Number"
    PERCENTAGE = "Percentage"
    RADIO = "Radio"
    RELATIONSHIP = "Relationship"
    TEXT_AREA = "TextArea"
    TEXT_FIELD = "TextField"
    UNIT = "Unit"
    YEAR_DATE = "YearDate"


class AnswerOptionType(Enum):
    """Defines the types of answers with options that can be used in a validators and reflect the answer types in the
    schema."""

    DROPDOWN = "Dropdown"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
