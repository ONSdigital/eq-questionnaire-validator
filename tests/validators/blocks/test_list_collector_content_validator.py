from app.validators.blocks import ListCollectorContentValidator
from app.validators.blocks.list_collector_validator import ListCollectorValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.utils import _open_and_load_schema_file


def test_invalid_list_collector_content_with_extra_list_collector_content_block():
    filename = "schemas/invalid/test_invalid_list_collector_content_page.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("list-collector-content")
    validator = ListCollectorContentValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": ListCollectorValidator.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
            "block_id": "list-collector-content",
            "list_name": "companies",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors
