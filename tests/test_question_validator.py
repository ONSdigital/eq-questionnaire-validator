from app.validation.question_validator import QuestionValidator


def test_invalid_id_in_answers_to_calculate():
    question = {
        "answers": [
            {
                "decimal_places": 2,
                "id": "breakdown-1",
                "label": "Breakdown 1",
                "type": "Number",
            },
            {
                "decimal_places": 2,
                "id": "breakdown-2",
                "label": "Breakdown 2",
                "type": "Number",
            },
        ],
        "calculations": [
            {
                "answer_id": "total-answer",
                "answers_to_calculate": [
                    "breakdown-1",
                    "breakdown-2",
                    "breakdown-3",
                    "breakdown-4",
                ],
                "calculation_type": "sum",
                "conditions": ["equals"],
            }
        ],
        "id": "breakdown-question",
        "title": "Breakdown",
        "type": "Calculated",
    }
    question_validator = QuestionValidator(question)
    question_validator.validate_answers_to_calculate()

    expected_error_messages = [
        {
            "message": "Answer does not exist within this question",
            "id": "breakdown-question",
            "answer_id": "breakdown-3",
        },
        {
            "message": "Answer does not exist within this question",
            "id": "breakdown-question",
            "answer_id": "breakdown-4",
        },
    ]

    assert expected_error_messages == question_validator.errors


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

    question_validator = QuestionValidator(question)
    question_validator.validate_date_range()

    expected_error_messages = [
        {
            "message": "The minimum period is greater than the maximum period",
            "id": "date-range-question",
        }
    ]

    assert expected_error_messages == expected_error_messages


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

    question_validator = QuestionValidator(question)
    question_validator.validate_date_range()

    expected_error_messages = [
        {
            "message": "Days/Months can not be used in period_limit for yyyy date range",
            "id": "date-range-question",
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

    question_validator = QuestionValidator(question)
    question_validator.validate_date_range()

    expected_error_messages = [
        {
            "message": "Days can not be used in period_limit for yyyy-mm date range",
            "id": "date-range-question",
        }
    ]

    assert expected_error_messages == question_validator.errors
