"""AnswerType and AnswerOptionType Enums."""

from enum import Enum


class AnswerType(Enum):
    """Defines the types of answers that can be provided in a questionnaire."""
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
    """Defines the types of answer options."""
    DROPDOWN = "Dropdown"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
