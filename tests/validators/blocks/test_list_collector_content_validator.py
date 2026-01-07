from app.error_messages import FOR_LIST_NEVER_POPULATED
from app.validators.blocks import ListCollectorContentValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


def test_invalid_list_collector_content_for_list():
    """Test invalid list collector content for list.

    Tests that when a for_list for a list collector content is not from supplementary data or
    another list collector it is found to be invalid.
    """
    filename = "schemas/invalid/test_invalid_supplementary_data_list_collector.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))

    errors = []
    for block_id in [
        "list-collector-employees",
        "list-collector-products",
    ]:
        block = questionnaire_schema.get_block(block_id)
        validator = ListCollectorContentValidator(block, questionnaire_schema)  # type: ignore
        # Validator always instantiates for this test schema (block always exists)
        errors += validator.validate()

    expected_errors = [
        {
            "message": FOR_LIST_NEVER_POPULATED,
            "block_id": "list-collector-employees",
            "list_name": "employees",
        },
        {
            "message": FOR_LIST_NEVER_POPULATED,
            "block_id": "list-collector-products",
            "list_name": "products",
        },
    ]

    assert expected_errors == errors
