from app.validators.blocks import BlockValidator
from app.validators.questionnaire_schema import QuestionnaireSchema
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_answer_action_redirect_to_list_add_block_no_params():
    filename = "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_block_no_params.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("anyone-else-live-here-block"),
        questionnaire_schema,
    )

    expected_error_messages = [
        {
            "message": validator.ACTION_PARAMS_MISSING,
            "block_id": "anyone-else-live-here-block",
        }
    ]

    validator.validate()

    assert expected_error_messages == validator.errors


def test_invalid_answer_action_redirect_to_list_add_block_unexpected_params():
    filename = "schemas/invalid/test_invalid_answer_action_redirect_to_list_add_block_unexpected_params.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("list-collector"), questionnaire_schema
    )

    expected_error_messages = [
        {
            "message": validator.ACTION_PARAMS_SHOULDNT_EXIST,
            "block_id": "list-collector",
        }
    ]

    validator.validate()

    assert expected_error_messages == validator.errors


def test_invalid_use_of_id_relationships_with_type():
    filename = "schemas/invalid/test_invalid_use_of_block_id_relationships.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("relationships"), questionnaire_schema
    )

    expected_error_messages = [
        {
            "message": validator.ID_RELATIONSHIPS_NOT_USED_WITH_RELATIONSHIP_COLLECTOR,
            "block_id": "relationships",
        }
    ]

    validator.validate()

    assert expected_error_messages == validator.errors


def test_invalid_self_reference():
    block = {
        "id": "block-1",
        "title": {
            "text": "test {simple_answer}",
            "placeholders": [
                {
                    "placeholder": "simple_answer",
                    "value": {"source": "answers", "identifier": "answer-1"},
                }
            ],
        },
    }

    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "answer-1": {
            "answer": {"id": "answer-1", "type": "TextField"},
            "block": "block-1",
        }
    }
    validator = BlockValidator(block, questionnaire_schema)
    validator.validate_placeholder_answer_self_references()

    expected_errors = [
        {
            "message": BlockValidator.PLACEHOLDER_ANSWER_SELF_REFERENCE,
            "identifier": "answer-1",
            "block_id": "block-1",
        }
    ]
    assert validator.errors == expected_errors
