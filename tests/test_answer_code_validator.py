import pytest

from app.validators.answer_code_validator import AnswerCodeValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file

CHECKBOX_ALLOWED_VALUES = [
    "None",
    "Ham & Cheese",
    "Ham",
    "Pepperoni",
    "Other",
]

CHECKBOX_ANSWER_OPTIONS = [
    {"label": "None", "value": "None"},
    {"label": "Ham & Cheese", "value": "Ham & Cheese"},
    {"label": "Ham", "value": "Ham"},
    {"label": "Pepperoni", "value": "Pepperoni"},
    {
        "description": "Choose any other topping",
        "detail_answer": {
            "id": "other-answer-mandatory",
            "label": "Please specify other",
            "mandatory": True,
            "type": "TextField",
        },
        "label": "Other",
        "value": "Other",
    },
]


@pytest.fixture
def load_schema():
    def _load(filename: str):
        return QuestionnaireSchema(_open_and_load_schema_file(filename))

    return _load


def run_validator(
    *,
    filename: str,
    answer_codes=None,
    version="0.0.3",
):
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator(
        version,
        answer_codes or questionnaire_schema.schema["answer_codes"],
        questionnaire_schema,
    )
    validator.validate()
    return validator.errors


def checkbox_codes_for_options(*entries):
    return [
        {
            "answer_id": "mandatory-checkbox-answer",
            "code": code,
            "answer_value": value,
        }
        for code, value in entries
    ]


def base_checkbox_answer_codes():
    return checkbox_codes_for_options(
        ("1a", "None"),
        ("1b", "Ham & Cheese"),
        ("1c", "Ham"),
        ("1d", "Pepperoni"),
        ("1e", "Other"),
    ) + [
        {"answer_id": "other-answer-mandatory", "code": "1f"},
    ]


def base_additional_answer_codes():
    return [
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]


def test_answer_code_validation_incorrect_data_version():
    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        version="0.0.1",
    )

    assert errors == [{"message": AnswerCodeValidator.INCORRECT_DATA_VERSION_FOR_ANSWER_CODES}]


def test_duplicate_answer_codes():
    answer_codes = base_checkbox_answer_codes() + [
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.DUPLICATE_ANSWER_CODE_FOUND,
            "duplicates": ["3"],
        },
        {
            "message": AnswerCodeValidator.DUPLICATE_ANSWER_ID_FOUND,
            "duplicates": ["name-answer"],
        },
    ]


def test_duplicate_answer_id_for_answer_code():
    answer_codes = base_checkbox_answer_codes() + [
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer", "code": "4"},
        {"answer_id": "name-answer-2", "code": "5"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.DUPLICATE_ANSWER_ID_FOUND,
            "duplicates": ["name-answer"],
        },
    ]


def test_answer_id_set_in_answer_codes_not_in_schema():
    answer_codes = base_checkbox_answer_codes() + [
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
        {"answer_id": "name-answer-3", "code": "5"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.ANSWER_CODE_ANSWER_ID_NOT_FOUND_IN_SCHEMA,
            "answer_codes.answer_id": "name-answer-3",
        },
    ]


def test_answer_value_set_for_answer_without_answer_options():
    answer_codes = base_checkbox_answer_codes() + [
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "answer_value": "missing_value", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.ANSWER_VALUE_SET_FOR_ANSWER_WITH_NO_OPTIONS,
            "answer_code": {
                "answer_id": "name-answer",
                "answer_value": "missing_value",
                "code": "3",
            },
            "answer_id": "name-answer",
        },
    ]


def test_answer_code_not_set_for_answer_found_in_schema():
    errors = run_validator(
        filename="schemas/invalid/test_invalid_answer_codes_answer_id_with_no_code.json",
    )

    assert errors == [
        {"message": AnswerCodeValidator.MISSING_ANSWER_CODE, "answer_id": "name-answer-2"},
    ]


def test_answer_code_missing_for_answer_options():
    answer_codes = (
        checkbox_codes_for_options(
            ("1a", "None"),
            ("1b", "Ham & Cheese"),
            ("1c", "Ham"),
            ("1e", "Other"),
        )
        + base_additional_answer_codes()
    )

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
            "answer_codes_for_options": checkbox_codes_for_options(
                ("1a", "None"),
                ("1b", "Ham & Cheese"),
                ("1c", "Ham"),
                ("1e", "Other"),
            ),
            "answer_options": CHECKBOX_ANSWER_OPTIONS,
            "answer_id": "mandatory-checkbox-answer",
        },
        {
            "message": AnswerCodeValidator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": checkbox_codes_for_options(
                ("1a", "None"),
                ("1b", "Ham & Cheese"),
                ("1c", "Ham"),
                ("1e", "Other"),
            ),
            "allowed_values": CHECKBOX_ALLOWED_VALUES,
        },
    ]


def test_answer_code_missing_for_answer_options_only_one_value_set():
    answer_codes = [
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Ham",
            "code": "1",
        },
    ] + base_additional_answer_codes()

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1",
                    "answer_value": "Ham",
                },
            ],
            "answer_options": CHECKBOX_ANSWER_OPTIONS,
            "answer_id": "mandatory-checkbox-answer",
        },
        {
            "message": AnswerCodeValidator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1",
                    "answer_value": "Ham",
                },
            ],
            "allowed_values": CHECKBOX_ALLOWED_VALUES,
        },
    ]


def test_more_than_one_answer_code_for_answer_options_when_no_value_set():
    answer_codes = base_checkbox_answer_codes() + [
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2a"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.DUPLICATE_ANSWER_ID_FOUND,
            "duplicates": ["mandatory-checkbox-answer-2"],
        },
        {
            "message": AnswerCodeValidator.MORE_THAN_ONE_ANSWER_CODE_SET_AT_PARENT_LEVEL,
            "answer_codes_for_options": [
                {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
                {"answer_id": "mandatory-checkbox-answer-2", "code": "2a"},
            ],
            "answer_options": ["None", "Mozzarella", "Onions"],
        },
    ]


def test_answer_code_with_duplicate_option_answer_values():
    answer_codes = checkbox_codes_for_options(
        ("1a", "None"),
        ("1b", "Ham & Cheese"),
        ("1c", "Ham"),
        ("1d", "Pepperoni"),
        ("1e", "Pepperoni"),
    ) + [
        {"answer_id": "other-answer-mandatory", "code": "1g"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "answer_value": "None",
                    "code": "1a",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "answer_value": "Ham & Cheese",
                    "code": "1b",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "answer_value": "Ham",
                    "code": "1c",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "answer_value": "Pepperoni",
                    "code": "1d",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "answer_value": "Pepperoni",
                    "code": "1e",
                },
            ],
            "allowed_values": CHECKBOX_ALLOWED_VALUES,
        },
    ]


def test_incorrect_answer_value_set_in_answer_code():
    answer_codes = (
        checkbox_codes_for_options(
            ("1a", "None"),
            ("1b", "Ham & Cheese"),
            ("1c", "Ham"),
            ("1d", "Pepperonis"),
            ("1e", "Other"),
        )
        + base_additional_answer_codes()
    )

    errors = run_validator(
        filename="schemas/valid/test_answer_codes.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "allowed_values": CHECKBOX_ALLOWED_VALUES,
            "answer_code": {
                "answer_id": "mandatory-checkbox-answer",
                "answer_value": "Pepperonis",
                "code": "1d",
            },
        },
    ]


def base_answer_codes_must_be_set_at_parent_level_for_dynamic_options():
    return [
        {"answer_id": "dynamic-radio-answer", "code": "2"},
        {
            "answer_id": "dynamic-radio-answer",
            "answer_value": "I don’t have a favourite",
            "code": "2a",
        },
        {"answer_id": "dynamic-dropdown-answer", "code": "3"},
        {
            "answer_id": "dynamic-dropdown-answer",
            "answer_value": "I don’t have a favourite",
            "code": "3a",
        },
    ]


def test_answer_codes_must_be_set_at_parent_level_for_dynamic_options():
    answer_codes = base_answer_codes_must_be_set_at_parent_level_for_dynamic_options() + [
        {
            "answer_id": "dynamic-checkbox-answer",
            "answer_value": "I don’t have a favourite",
            "code": "1a",
        },
    ]

    errors = run_validator(
        filename="schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.DYNAMIC_ANSWER_OPTION_MUST_HAVE_ANSWER_CODE_SET_AT_TOP_LEVEL,
            "answer_codes_for_options": [
                {
                    "answer_id": "dynamic-checkbox-answer",
                    "answer_value": "I don’t have a favourite",
                    "code": "1a",
                },
            ],
        },
    ]


def test_answer_codes_allowed_at_parent_and_value_level_for_dynamic_options():
    errors = run_validator(
        filename="schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json",
    )

    assert not errors


def test_invalid_value_in_answer_code_for_dynamic_options():
    answer_codes = base_answer_codes_must_be_set_at_parent_level_for_dynamic_options() + [
        {"answer_id": "dynamic-checkbox-answer", "code": "1"},
        {
            "answer_id": "dynamic-checkbox-answer",
            "answer_value": "No favourite",
            "code": "1a",
        },
    ]

    errors = run_validator(
        filename="schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "allowed_values": ["I don’t have a favourite"],
            "answer_code": {
                "answer_id": "dynamic-checkbox-answer",
                "answer_value": "No favourite",
                "code": "1a",
            },
        },
    ]


def base_missing_answer_codes_for_list_add_questions():
    return [
        {"answer_id": "any-companies-or-branches-answer", "code": "1"},
        {"answer_id": "company-or-branch-name", "code": "1a"},
        {"answer_id": "authorised-insurer-radio", "code": "1c"},
        {"answer_id": "any-other-companies-or-branches-answer", "code": "2"},
        {"answer_id": "confirmation-checkbox-answer", "code": "3"},
        {"answer_id": "anyone-else", "code": "4"},
        {"answer_id": "householder-checkbox-answer", "code": "5"},
    ]


def test_missing_answer_codes_for_list_add_questions():
    errors = run_validator(
        filename="schemas/valid/test_answer_codes_list_collector.json",
        answer_codes=base_missing_answer_codes_for_list_add_questions(),
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.MISSING_ANSWER_CODE,
            "answer_id": "registration-number",
        },
        {
            "message": AnswerCodeValidator.MISSING_ANSWER_CODE,
            "answer_id": "first-name",
        },
        {
            "message": AnswerCodeValidator.MISSING_ANSWER_CODE,
            "answer_id": "last-name",
        },
    ]


def test_invalid_answer_codes_for_list_collector_remove_question():
    answer_codes = base_missing_answer_codes_for_list_add_questions() + [
        {"answer_id": "registration-number", "code": "1b"},
        {"answer_id": "remove-company-confirmation", "code": "5a"},
    ]

    errors = run_validator(
        filename="schemas/valid/test_answer_codes_list_collector.json",
        answer_codes=answer_codes,
    )

    assert errors == [
        {
            "message": AnswerCodeValidator.INVALID_ANSWER_CODE_FOR_LIST_COLLECTOR,
            "answer_id": "remove-company-confirmation",
        },
        {
            "message": AnswerCodeValidator.MISSING_ANSWER_CODE,
            "answer_id": "first-name",
        },
        {
            "message": AnswerCodeValidator.MISSING_ANSWER_CODE,
            "answer_id": "last-name",
        },
    ]
