from app import error_messages
from app.validators.blocks import PrimaryPersonListCollectorValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_primary_person_list_collector_bad_answer_reference_ids():
    filename = (
        "schemas/invalid/test_invalid_primary_person_list_collector_bad_answer_id.json"
    )
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("primary-person-list-collector")

    validator = PrimaryPersonListCollectorValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": error_messages.ADD_OR_EDIT_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK,
            "referenced_id": "fake-answer-id",
            "block_id": "primary-person-list-collector",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_primary_person_list_collector_with_different_add_block_answer_ids():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_different_answer_ids_multi_collectors.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("primary-person-list-collector")

    validator = PrimaryPersonListCollectorValidator(block, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.NON_UNIQUE_ANSWER_ID_FOR_PRIMARY_LIST_COLLECTOR_ADD_OR_EDIT,
            "list_name": "people",
            "block_id": "primary-person-list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_primary_person_invalid_list_collector_non_radio():
    filename = (
        "schemas/invalid/test_invalid_primary_person_list_collector_no_radio.json"
    )
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = PrimaryPersonListCollectorValidator(
        questionnaire_schema.get_block("primary-person-list-collector"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR,
            "block_id": "primary-person-list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_primary_person_list_collector_with_no_add_option():
    filename = "schemas/invalid/test_invalid_primary_person_list_collector_bad_answer_value.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = PrimaryPersonListCollectorValidator(
        questionnaire_schema.get_block("primary-person-list-collector"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.NON_EXISTENT_PRIMARY_PERSON_LIST_COLLECTOR_ANSWER_VALUE,
            "block_id": "primary-person-list-collector",
        }
    ]

    assert expected_errors == validator.errors
