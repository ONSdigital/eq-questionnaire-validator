from app.validators.blocks import ListCollectorValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_list_collector_with_different_answer_ids_in_add_and_edit():
    filename = "schemas/invalid/test_invalid_list_collector_with_different_answer_ids_in_add_and_edit.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("list-collector")
    validator = ListCollectorValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": validator.LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH,
            "block_id": "list-collector",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_list_collector_with_different_add_block_answer_ids():
    filename = "schemas/invalid/test_invalid_list_collector_with_different_add_block_answer_ids.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("list-collector")
    validator = ListCollectorValidator(block, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": validator.NON_UNIQUE_ANSWER_ID_FOR_LIST_COLLECTOR_ADD,
            "list_name": "people",
            "block_id": "list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_non_radio():
    filename = "schemas/invalid/test_invalid_list_collector_non_radio.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = ListCollectorValidator(
        questionnaire_schema.get_block("list-collector"), questionnaire_schema
    )
    validator.validate()

    expected_error_messages = [
        {"message": validator.NO_RADIO_FOR_LIST_COLLECTOR, "block_id": "list-collector"}
    ]

    assert expected_error_messages == validator.errors


def test_invalid_list_collector_with_no_add_answer_action():
    filename = (
        "schemas/invalid/test_invalid_list_collector_with_no_add_answer_action.json"
    )

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = ListCollectorValidator(
        questionnaire_schema.get_block("list-collector"), questionnaire_schema
    )
    validator.validate()

    expected_errors = [
        {
            "message": validator.NO_REDIRECT_TO_LIST_ADD_BLOCK_ACTION,
            "block_id": "list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_with_no_remove_answer_action():
    filename = (
        "schemas/invalid/test_invalid_list_collector_with_no_remove_answer_action.json"
    )

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = ListCollectorValidator(
        questionnaire_schema.get_block("list-collector"), questionnaire_schema
    )
    validator.validate()

    expected_errors = [
        {
            "message": validator.NO_REMOVE_LIST_ITEM_AND_ANSWERS_ACTION,
            "block_id": "list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_same_name_answer_id_reference():
    filename = "schemas/invalid/test_invalid_list_collector_same_name_answer_ids.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = ListCollectorValidator(
        questionnaire_schema.get_block("list-collector"), questionnaire_schema
    )
    validator.validate()

    expected_errors = [
        {
            "message": validator.MISSING_SAME_NAME_ANSWER_ID,
            "block_id": "list-collector",
            "answer_id": "surname",
        }
    ]

    assert expected_errors == validator.errors
