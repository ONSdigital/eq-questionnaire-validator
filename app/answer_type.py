from enum import Enum


class AnswerType(Enum):
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
    DROPDOWN = "Dropdown"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
