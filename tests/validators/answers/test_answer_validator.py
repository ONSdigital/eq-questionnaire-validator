from app.validators.answers.answer_validator import AnswerValidator
from app.validators.answers.date_answer_validator import DateAnswerValidator
from app.validators.answers.number_answer_validator import NumberAnswerValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_mismatching_answer_label_and_value():
    answer = {
        "type": "Radio",
        "id": "correct-answer",
        "mandatory": False,
        "options": [
            {"label": "Yes it is {name}", "value": "Yes it is"},
            {"label": "Nope", "value": "No"},
        ],
    }

    validator = AnswerValidator(answer)

    expected_errors = [
        {
            "message": validator.ANSWER_LABEL_VALUE_MISMATCH,
            "answer_id": "correct-answer",
            "label": "Yes it is {name}",
            "value": "Yes it is",
        },
        {
            "message": validator.ANSWER_LABEL_VALUE_MISMATCH,
            "answer_id": "correct-answer",
            "label": "Nope",
            "value": "No",
        },
    ]

    validator.validate_labels_and_values_match()

    assert expected_errors == validator.errors


def test_number_of_decimals():
    answer = {
        "decimal_places": 10,
        "id": "answer-5",
        "label": "Too many decimals declared",
        "mandatory": False,
        "type": "Number",
    }

    validator = NumberAnswerValidator(answer)

    validator.validate_decimals()

    assert validator.errors[0] == {
        "message": validator.DECIMAL_PLACES_TOO_LONG,
        "decimal_places": 10,
        "limit": 6,
        "answer_id": "answer-5",
    }


def test_minimum_value():
    answer = {
        "id": "answer-4",
        "label": "Max/Min out of system limits",
        "mandatory": False,
        "maximum": {"value": 99999999999},
        "minimum": {"value": -99999999999},
        "type": "Number",
    }

    validator = NumberAnswerValidator(answer)

    validator.validate_value_in_limits()

    assert validator.errors[0] == {
        "message": validator.MINIMUM_LESS_THAN_LIMIT,
        "value": -99999999999,
        "limit": -999999999,
        "answer_id": "answer-4",
    }

    assert validator.errors[1] == {
        "message": validator.MAXIMUM_GREATER_THAN_LIMIT,
        "value": 99999999999,
        "limit": 9999999999,
        "answer_id": "answer-4",
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

    answer_validator = DateAnswerValidator(answer)

    assert not answer_validator.is_offset_date_valid()


def test_invalid_answer_default():
    answer = {
        "default": 0,
        "id": "answer-7",
        "label": "Default with Mandatory",
        "mandatory": True,
        "type": "Number",
    }

    validator = NumberAnswerValidator(answer)
    validator.validate_mandatory_has_no_default()

    assert validator.errors[0] == {
        "message": validator.DEFAULT_ON_MANDATORY,
        "answer_id": "answer-7",
    }


def test_are_decimal_places_valid():
    answer = {
        "calculated": True,
        "description": "The total percentages should be 100%",
        "id": "total-percentage",
        "label": "Total",
        "mandatory": False,
        "q_code": "10002",
        "type": "Percentage",
        "maximum": {"value": 100},
    }

    validator = NumberAnswerValidator(answer)
    validator.validate_decimal_places()

    assert validator.errors[0] == {
        "message": validator.DECIMAL_PLACES_UNDEFINED,
        "answer_id": "total-percentage",
    }


def test_unique_answer_options():
    answer = {
        "id": "duplicate-country-answer",
        "label": "",
        "type": "Checkbox",
        "options": [
            {"label": "India", "value": "India"},
            {"label": "Azerbaijan", "value": "Azerbaijan"},
            {"label": "India", "value": "India"},
            {"label": "Malta", "value": "Malta"},
        ],
    }

    validator = AnswerValidator(answer)
    validator.validate_duplicate_options()

    assert validator.errors == [
        {
            "message": validator.DUPLICATE_LABEL_FOUND,
            "answer_id": "duplicate-country-answer",
            "label": "India",
        },
        {
            "message": validator.DUPLICATE_VALUE_FOUND,
            "answer_id": "duplicate-country-answer",
            "value": "India",
        },
    ]


def test_invalid_range():
    answer = {
        "id": "answer-3",
        "label": "Invalid References",
        "mandatory": False,
        "maximum": {"value": {"identifier": "answer-5", "source": "answers"}},
        "minimum": {"value": {"identifier": "answer-4", "source": "answers"}},
        "type": "Percentage",
    }
    validator = NumberAnswerValidator(answer)

    validator.validate_referred_numeric_answer({"answer-3": {"min": None, "max": None}})

    expected_errors = [
        {
            "message": validator.MINIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-4",
            "answer_id": "answer-3",
        },
        {
            "message": validator.MAXIMUM_CANNOT_BE_SET_WITH_ANSWER,
            "referenced_id": "answer-5",
            "answer_id": "answer-3",
        },
    ]

    assert validator.errors == expected_errors


def test_invalid_numeric_answers():
    validator = NumberAnswerValidator(
        {
            "decimal_places": 2,
            "id": "answer-1",
            "label": "Answer 1",
            "mandatory": False,
            "type": "Number",
        }
    )
    validator.validate_referred_numeric_answer_decimals(
        {
            "answer-1": {
                "min_referred": "answer-2",
                "max_referred": None,
                "decimal_places": 2,
            },
            "answer-2": {"decimal_places": 3},
        }
    )

    expected_errors = [
        {
            "message": validator.GREATER_DECIMALS_ON_ANSWER_REFERENCE,
            "referenced_id": "answer-2",
            "answer_id": "answer-1",
        }
    ]

    assert validator.errors == expected_errors


def test_invalid_answer_action():
    filename = (
        "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_question.json"
    )
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    answer = questionnaire_schema.get_answer("anyone-else-live-here-answer")
    validator = AnswerValidator(
        answer,
        list_names=questionnaire_schema.list_names,
        block_ids=questionnaire_schema.block_ids,
    )

    expected_error_messages = [
        {
            "message": validator.LIST_NAME_MISSING,
            "answer_id": "anyone-else-live-here-answer",
            "list_name": "non-existent-list-name",
        },
        {
            "message": validator.BLOCK_ID_MISSING,
            "block_id": "non-existent-block-id",
            "answer_id": "anyone-else-live-here-answer",
        },
    ]

    validator.validate()

    assert expected_error_messages == validator.errors
