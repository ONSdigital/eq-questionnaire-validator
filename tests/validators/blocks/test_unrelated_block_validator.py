from app.validators.blocks.unrelated_block_validator import UnrelatedBlockValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_actions():
    filename = "schemas/invalid/test_invalid_relationships_unrelated.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("relationships").get("unrelated_block")
    validator = UnrelatedBlockValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": validator.ACTION_PARAMS_MISSING,
            "block_id": "related-to-anyone-else",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors
