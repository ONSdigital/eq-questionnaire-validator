from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from tests.conftest import get_mock_schema_with_data_version


def test_number_of_decimals():
    answer = {
        "decimal_places": 10,
        "id": "answer-5",
        "label": "Too many decimals declared",
        "mandatory": False,
        "type": "Number",
    }

    validator = NumberAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )

    validator.validate_decimals()

    assert validator.errors[0] == {
        "message": validator.DECIMAL_PLACES_TOO_LONG,
        "decimal_places": 10,
        "limit": 6,
        "answer_id": "answer-5",
    }


def test_invalid_single_date_period():
    answer = {
        "id": "date-range-from",
        "label": "Period from",
        "mandatory": True,
        "maximum": {"offset_by": {"days": 2}, "value": "2017-06-11"},
        "minimum": {"offset_by": {"days": -19}, "value": "now"},
        "type": "Date",
    }

    answer_validator = DateAnswerValidator(
        answer, get_mock_schema_with_data_version("0.0.3")
    )

    assert not answer_validator.is_offset_date_valid()
