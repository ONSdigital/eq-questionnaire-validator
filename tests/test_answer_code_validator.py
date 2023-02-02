from app.validators.answer_code_validator import AnswerCodeValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_answer_code_validation_incorrect_data_version():
    filename = "schemas/valid/test_answer_codes.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator(
        "0.0.1", questionnaire_schema.schema["answer_codes"], questionnaire_schema
    )

    validator.validate()

    expected_errors = [{"message": validator.INCORRECT_DATA_VERSION_FOR_ANSWER_CODES}]

    assert validator.errors == expected_errors


def test_duplicate_answer_codes():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Pepperoni",
            "code": "1d",
        },
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Other",
            "code": "1e",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {"message": validator.DUPLICATE_ANSWER_CODE_FOUND, "duplicates": ["3"]}
    ]

    assert validator.errors == expected_errors


def test_answer_id_set_in_answer_codes_not_in_schema():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Pepperoni",
            "code": "1d",
        },
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Other",
            "code": "1e",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
        {"answer_id": "name-answer-3", "code": "5"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.ANSWER_CODE_ANSWER_ID_NOT_FOUND_IN_SCHEMA,
            "answer_id": "name-answer-3",
        }
    ]

    assert validator.errors == expected_errors


def test_answer_code_not_set_for_answer_found_in_schema():
    filename = "schemas/invalid/test_invalid_answer_codes_answer_id_with_no_code.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator(
        "0.0.3", questionnaire_schema.schema["answer_codes"], questionnaire_schema
    )

    validator.validate()

    expected_errors = [
        {"message": validator.MISSING_ANSWER_CODE, "answer_id": "name-answer-2"}
    ]

    assert validator.errors == expected_errors


def test_answer_code_missing_for_answer_options():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Other",
            "code": "1e",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1a",
                    "answer_value": "None",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1b",
                    "answer_value": "Ham & Cheese",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1c",
                    "answer_value": "Ham",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1e",
                    "answer_value": "Other",
                },
            ],
            "answer_options": [
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
            ],
        },
        {
            "message": validator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1a",
                    "answer_value": "None",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1b",
                    "answer_value": "Ham & Cheese",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1c",
                    "answer_value": "Ham",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1e",
                    "answer_value": "Other",
                },
            ],
        },
    ]

    assert validator.errors == expected_errors


def test_answer_code_missing_for_answer_options_only_one_value_set():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Ham",
            "code": "1",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.ANSWER_CODE_MISSING_FOR_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1",
                    "answer_value": "Ham",
                },
            ],
            "answer_options": [
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
            ],
        },
        {
            "message": validator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1",
                    "answer_value": "Ham",
                },
            ],
        },
    ]

    assert validator.errors == expected_errors


def test_more_than_one_answer_code_for_answer_options_when_no_value_set():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Pepperoni",
            "code": "1d",
        },
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Other",
            "code": "1e",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2a"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.MORE_THAN_ONE_ANSWER_CODE_SET_AT_PARENT_LEVEL,
            "answer_codes_for_options": [
                {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
                {"answer_id": "mandatory-checkbox-answer-2", "code": "2a"},
            ],
            "answer_options": [
                {"label": "None", "value": "None"},
                {"label": "Mozzarella", "value": "Mozzarella"},
                {"label": "Onions", "value": "Onions"},
            ],
        }
    ]

    assert validator.errors == expected_errors


def test_answer_code_with_duplicate_option_answer_values():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
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
        {"answer_id": "other-answer-mandatory", "code": "1g"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
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
        }
    ]

    assert validator.errors == expected_errors


def test_incorrect_answer_value_set_in_answer_code():
    filename = "schemas/valid/test_answer_codes.json"

    answer_codes = [
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
        {"answer_id": "mandatory-checkbox-answer", "answer_value": "Ham", "code": "1c"},
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Pepperonis",
            "code": "1d",
        },
        {
            "answer_id": "mandatory-checkbox-answer",
            "answer_value": "Other",
            "code": "1e",
        },
        {"answer_id": "other-answer-mandatory", "code": "1f"},
        {"answer_id": "mandatory-checkbox-answer-2", "code": "2"},
        {"answer_id": "name-answer", "code": "3"},
        {"answer_id": "name-answer-2", "code": "4"},
    ]

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1a",
                    "answer_value": "None",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1b",
                    "answer_value": "Ham & Cheese",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1c",
                    "answer_value": "Ham",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1d",
                    "answer_value": "Pepperonis",
                },
                {
                    "answer_id": "mandatory-checkbox-answer",
                    "code": "1e",
                    "answer_value": "Other",
                },
            ],
            "answer_value": "Pepperonis",
        }
    ]

    assert validator.errors == expected_errors


def test_answer_codes_must_be_set_at_parent_level_for_dynamic_options():
    filename = "schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer_codes = [
        {
            "answer_id": "dynamic-checkbox-answer",
            "answer_value": "I don’t have a favourite",
            "code": "1a",
        },
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

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.DYNAMIC_ANSWER_OPTION_MUST_HAVE_ANSWER_CODE_SET_AT_TOP_LEVEL,
            "answer_codes_for_options": [
                {
                    "answer_id": "dynamic-checkbox-answer",
                    "answer_value": "I don’t have a favourite",
                    "code": "1a",
                },
            ],
        }
    ]

    assert validator.errors == expected_errors


def test_answer_codes_allowed_at_parent_and_value_level_for_dynamic_options():
    filename = "schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = AnswerCodeValidator(
        "0.0.3", questionnaire_schema.schema["answer_codes"], questionnaire_schema
    )

    validator.validate()

    assert not validator.errors


def test_invalid_value_in_answer_code_for_dynamic_options():
    filename = "schemas/valid/test_dynamic_answer_options_dynamic_date_driven.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    answer_codes = [
        {"answer_id": "dynamic-checkbox-answer", "code": "1"},
        {
            "answer_id": "dynamic-checkbox-answer",
            "answer_value": "No favourite",
            "code": "1a",
        },
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

    validator = AnswerCodeValidator("0.0.3", answer_codes, questionnaire_schema)

    validator.validate()

    expected_errors = [
        {
            "message": validator.INCORRECT_VALUE_FOR_ANSWER_CODE_WITH_ANSWER_OPTIONS,
            "answer_codes_for_options": [
                {"answer_id": "dynamic-checkbox-answer", "code": "1"},
                {
                    "answer_id": "dynamic-checkbox-answer",
                    "code": "1a",
                    "answer_value": "No favourite",
                },
            ],
            "answer_value": "No favourite",
        }
    ]

    assert validator.errors == expected_errors
