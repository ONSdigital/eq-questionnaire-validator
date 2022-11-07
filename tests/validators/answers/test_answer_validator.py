from app.validators.answers import get_answer_validator
from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.questionnaire_validator import QuestionnaireValidator
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


def test_confirmation_question_q_code():
    filename = "schemas/valid/test_q_codes.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = schema.get_answer("confirmation-1-answer")
    answer["q_code"] = "1"

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "answer_id": "confirmation-1-answer",
            "message": validator.CONFIRMATION_QUESTION_HAS_Q_CODE,
        }
    ]

    assert expected_error_messages == validator.errors


def test_data_version_0_0_3_q_code():
    # valid schema for test purposes, q_code is injected
    filename = "schemas/valid/test_interstitial_instruction.json"
    schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = schema.get_answer("favourite-lunch")
    answer["q_code"] = "0"

    validator = get_answer_validator(answer, schema)
    validator.validate()

    expected_error_messages = [
        {
            "answer_id": "favourite-lunch",
            "message": validator.DATA_VERSION_NOT_0_0_1_Q_CODE_PRESENT,
        }
    ]

    assert expected_error_messages == validator.errors


def test_invalid_q_codes():
    filename = "schemas/invalid/test_invalid_q_code.json"
    json_to_validate = _open_and_load_schema_file(filename)
    questionnaire_validator = QuestionnaireValidator(json_to_validate)
    questionnaire_validator.validate()

    expected_error_messages = [
        {
            "answer_id": "radio-1-answer",
            "message": AnswerValidator.ANSWER_MISSING_Q_CODE,
        },
        {
            "answer_id": "radio-1-answer",
            "message": AnswerValidator.NON_CHECKBOX_OPTION_HAS_Q_CODE,
        },
        {
            "answer_id": "radio-1-answer",
            "message": AnswerValidator.DETAIL_ANSWER_MISSING_Q_CODE,
        },
        {
            "answer_id": "dropdown-1-answer",
            "message": AnswerValidator.ANSWER_MISSING_Q_CODE,
        },
        {
            "answer_id": "dropdown-1-answer",
            "message": AnswerValidator.NON_CHECKBOX_OPTION_HAS_Q_CODE,
        },
        {
            "answer_id": "dropdown-1-answer",
            "message": AnswerValidator.DETAIL_ANSWER_MISSING_Q_CODE,
        },
        {
            "answer_id": "checkbox-1-answer",
            "message": AnswerValidator.CHECKBOX_DETAIL_ANSWER_HAS_Q_CODE,
        },
        {
            "answer_id": "checkbox-1-answer",
            "message": AnswerValidator.CHECKBOX_ANSWER_AND_OPTIONS_Q_CODE_MUTUALLY_EXCLUSIVE,
        },
        {
            "answer_id": "checkbox-2-answer",
            "message": AnswerValidator.CHECKBOX_ANSWER_OR_OPTIONS_MUST_HAVE_Q_CODES,
        },
    ]

    assert expected_error_messages == questionnaire_validator.errors
