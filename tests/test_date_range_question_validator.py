from app.validation.questions.date_range_question_validator import (
    DateRangeQuestionValidator,
)


def test_invalid_date_range():
    question = {
        "answers": [
            {
                "id": "date-range-from",
                "label": "Period from",
                "mandatory": True,
                "type": "Date",
            },
            {
                "id": "date-range-to",
                "label": "Period to",
                "mandatory": True,
                "type": "Date",
            },
        ],
        "id": "date-range-question",
        "period_limits": {
            "maximum": {"days": 20, "months": 1},
            "minimum": {"days": 23, "years": 1},
        },
        "title": "Enter Date Range",
        "type": "DateRange",
    }

    question_validator = DateRangeQuestionValidator(question)
    question_validator.validate()

    expected_error_messages = [
        {
            "message": "The minimum period is greater than the maximum period",
            "question_id": "date-range-question",
        }
    ]

    assert expected_error_messages == question_validator.errors


def test_invalid_yyyy_date_range_period():
    question = {
        "answers": [
            {
                "id": "date-range-from",
                "label": "Period from",
                "mandatory": True,
                "minimum": {
                    "value": {"source": "metadata", "identifier": "ref_p_start_date"},
                    "offset_by": {"years": -1},
                },
                "type": "YearDate",
            },
            {
                "id": "date-range-to",
                "label": "Period to",
                "mandatory": True,
                "maximum": {
                    "value": {"source": "metadata", "identifier": "ref_p_end_date"},
                    "offset_by": {"years": 2},
                },
                "type": "YearDate",
            },
        ],
        "id": "date-range-question",
        "period_limits": {"maximum": {"months": 2}, "minimum": {"days": 1}},
        "title": "Enter Date Range",
        "type": "DateRange",
    }

    question_validator = DateRangeQuestionValidator(question)
    question_validator.validate()

    expected_error_messages = [
        {
            "message": "Days/Months can not be used in period_limit for yyyy date range",
            "question_id": "date-range-question",
        }
    ]

    assert expected_error_messages == question_validator.errors


def test_invalid_mm_yyyy_date_range_period():
    question = {
        "answers": [
            {
                "id": "date-range-from",
                "label": "Period from",
                "mandatory": True,
                "minimum": {
                    "value": {"identifier": "ref_p_start_date", "source": "metadata"},
                    "offset_by": {"months": -1},
                },
                "type": "MonthYearDate",
            },
            {
                "id": "date-range-to",
                "label": "Period to",
                "mandatory": True,
                "maximum": {
                    "value": {"identifier": "ref_p_end_date", "source": "metadata"},
                    "offset_by": {"months": 2},
                },
                "type": "MonthYearDate",
            },
        ],
        "id": "date-range-question",
        "period_limits": {
            "maximum": {"days": 5, "months": 2},
            "minimum": {"days": 7, "months": 1},
        },
        "title": "Enter Date Range",
        "type": "DateRange",
    }

    question_validator = DateRangeQuestionValidator(question)
    question_validator.validate()

    expected_error_messages = [
        {
            "message": "Days can not be used in period_limit for yyyy-mm date range",
            "question_id": "date-range-question",
        }
    ]

    assert expected_error_messages == question_validator.errors
