from app.validators.answers import get_answer_validator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.conftest import get_mock_schema_with_data_version
from tests.test_questionnaire_validator import _open_and_load_schema_file


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


def test_present_answer_q_code_general():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "q_code": "10",
        "id": "general-1-answer",
        "type": "Number",
        "label": "Leave blank",
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = []

    assert expected_error_messages == validator.errors


def test_missing_answer_q_code_general():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "id": "general-1-answer",
        "type": "Number",
        "label": "Leave blank",
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_MISSING_Q_CODE,
            "answer_id": "general-1-answer",
        },
    ]

    assert expected_error_messages == validator.errors


def test_missing_option_q_code_checkbox():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "id": "checkbox-1-answer",
        "mandatory": True,
        "options": [
            {
                "label": "None",
                "value": "None",
            },
            {
                "label": "Other",
                "q_code": "6",
                "description": "Choose any other topping",
                "value": "Other",
                "detail_answer": {
                    "mandatory": True,
                    "id": "checkbox-1-other-answer",
                    "label": "Please specify other",
                    "type": "TextField",
                },
            },
        ],
        "type": "Checkbox",
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.OPTION_MISSING_Q_CODE,
            "answer_id": "checkbox-1-answer",
        },
    ]

    assert expected_error_messages == validator.errors


def test_missing_answer_q_code_radio():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "type": "Radio",
        "id": "radio-1-answer",
        "mandatory": True,
        "options": [
            {"label": "Coffee", "value": "Coffee"},
            {"label": "Tea", "value": "Tea"},
        ],
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.ANSWER_MISSING_Q_CODE,
            "answer_id": "radio-1-answer",
        },
    ]

    assert expected_error_messages == validator.errors


def test_missing_detail_answer_q_code_radio():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "type": "Radio",
        "id": "radio-2-answer",
        "q_code": "8",
        "options": [
            {"label": "Toast", "value": "Toast"},
            {
                "label": "Other",
                "description": "An answer is required.",
                "value": "Other",
                "detail_answer": {
                    "id": "radio-2-other-answer",
                    "label": "Please specify other",
                    "type": "TextField",
                },
            },
        ],
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "message": validator.DETAIL_ANSWER_MISSING_Q_CODE,
            "answer_id": "radio-2-answer",
        },
    ]

    assert expected_error_messages == validator.errors


def test_missing_detail_answer_q_code_checkbox():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = {
        "id": "checkbox-1-answer",
        "options": [
            {"label": "None", "value": "None", "q_code": "0"},
            {
                "label": "Other",
                "q_code": "6",
                "description": "Choose any other topping",
                "value": "Other",
                "detail_answer": {
                    "id": "checkbox-1-other-answer",
                    "label": "Please specify other",
                    "type": "TextField",
                },
            },
        ],
        "type": "Checkbox",
    }

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = []

    assert expected_error_messages == validator.errors
