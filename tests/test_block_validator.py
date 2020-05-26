from app.validators.blocks import BlockValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_reference():
    known_identifiers = ["answer-1", "answer-2"]

    questionnaire_schema = QuestionnaireSchema({})
    validator = BlockValidator({"id": "block-1"}, questionnaire_schema)
    validator.questionnaire_schema.answers_with_context = {
        "answer-1": {
            "answer": {
                "decimal_places": 2,
                "id": "answer-1",
                "label": "Answer 1",
                "mandatory": False,
                "type": "Number",
            },
            "block": "block-1",
        }
    }

    validator.validate_answer_source_reference(
        identifiers=known_identifiers, current_block_id="block-1"
    )

    expected_errors = [
        {
            "message": BlockValidator.ANSWER_SELF_REFERENCE,
            "referenced_id": "answer-1",
            "block_id": "block-1",
        },
        {
            "message": BlockValidator.ANSWER_REFERENCE_INVALID,
            "referenced_id": "answer-2",
            "block_id": "block-1",
        },
    ]
    assert validator.errors == expected_errors


def test_invalid_placeholder_list_reference():
    filename = "schemas/invalid/test_invalid_placeholder_plurals.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("block1"), questionnaire_schema
    )
    validator.validate_list_source_reference(["people"], "block1")

    expected_errors = [
        {
            "message": BlockValidator.LIST_REFERENCE_INVALID,
            "block_id": "block1",
            "id": "people",
        }
    ]

    assert expected_errors == validator.errors
