from app.validators.blocks import RelationshipCollectorValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_relationship_multiple_answers():
    filename = "schemas/invalid/test_invalid_relationship_multiple_answers.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("relationships")
    validator = RelationshipCollectorValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": validator.RELATIONSHIP_COLLECTOR_HAS_MULTIPLE_ANSWERS,
            "block_id": "relationships",
        }
    ]

    validator.validate()

    assert validator.errors == expected_errors


def test_invalid_relationship_wrong_answer_type():
    filename = "schemas/invalid/test_invalid_relationship_wrong_answer_type.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    block = questionnaire_schema.get_block("relationships")
    validator = RelationshipCollectorValidator(block, questionnaire_schema)

    expected_errors = [
        {
            "message": validator.RELATIONSHIP_COLLECTOR_HAS_INVALID_ANSWER_TYPE,
            "block_id": "relationships",
        }
    ]

    validator.validate_answer_type()

    assert validator.errors == expected_errors
