from app.validators.blocks import ListCollectorValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


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


def test_invalid_list_collector_with_answer_id_used_elsewhere():
    filename = "schemas/invalid/test_invalid_list_collector_with_duplicate_answer_id_used_elsewhere.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("list-collector")
    validator = ListCollectorValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": validator.LIST_COLLECTOR_ANSWER_ID_USED_ELSEWHERE,
            "block_id": "list-collector",
            "list_child_block_name": "add_block",
        },
        {
            "message": validator.LIST_COLLECTOR_ANSWER_ID_USED_ELSEWHERE,
            "block_id": "list-collector",
            "list_child_block_name": "edit_block",
        },
        {
            "message": validator.LIST_COLLECTOR_ANSWER_ID_USED_ELSEWHERE,
            "block_id": "list-collector",
            "list_child_block_name": "remove_block",
        },
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
            "message": validator.DIFFERENT_LIST_COLLECTOR_ADD_BLOCKS_FOR_SAME_LIST,
            "list_name": "people",
            "block_id": "list-collector",
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_with_duplicate_add_block_answer_id_for_different_list_collector():
    filename = "schemas/invalid/test_invalid_list_collector_with_duplicate_answer_ids_for_different_list_collector.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("list-collector")
    validator = ListCollectorValidator(block, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": validator.DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR,
            "list_name": "people",
            "list_child_block_name": "add_block",
            "block_id": "list-collector",
            "other_list_name": "visitor",
            "other_list_block_id": "visitor-list-collector",
        },
        {
            "message": validator.DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR,
            "list_name": "people",
            "list_child_block_name": "edit_block",
            "block_id": "list-collector",
            "other_list_name": "visitor",
            "other_list_block_id": "visitor-list-collector",
        },
        {
            "message": validator.DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR,
            "list_name": "people",
            "list_child_block_name": "remove_block",
            "block_id": "list-collector",
            "other_list_name": "visitor",
            "other_list_block_id": "visitor-list-collector",
        },
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


def test_invalid_list_collector_repeating_blocks_multiple_list_collectors_same_section():
    filename = "schemas/invalid/test_invalid_list_collector_repeating_blocks_multiple_list_collectors_same_section.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = ListCollectorValidator(
        questionnaire_schema.get_block("any-other-companies-or-branches"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "block_id": "any-other-companies-or-branches",
            "list_name": "companies",
            "message": validator.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
        }
    ]

    assert expected_errors == validator.errors

    validator = ListCollectorValidator(
        questionnaire_schema.get_block("any-other-companies-or-branches-again"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "block_id": "any-other-companies-or-branches-again",
            "list_name": "companies",
            "message": validator.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
        }
    ]

    assert expected_errors == validator.errors


def test_invalid_list_collector_for_supplementary_list():
    """
    Tests that you cannot have a normal list collector for a supplementary list
    """
    filename = "schemas/invalid/test_invalid_supplementary_data_list_collector.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    validator = ListCollectorValidator(
        questionnaire_schema.get_block("list-collector-additional"),
        questionnaire_schema,
    )
    validator.validate()

    expected_errors = [
        {
            "message": ListCollectorValidator.LIST_COLLECTOR_FOR_SUPPLEMENTARY_LIST_IS_INVALID,
            "block_id": "list-collector-additional",
            "list_name": "additional-employees",
        }
    ]

    assert expected_errors == validator.errors
