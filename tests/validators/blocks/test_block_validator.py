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

    validator.validate_answer_source_reference(identifiers=known_identifiers)

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


def test_invalid_composite_answer_in_selector():
    questionnaire_schema = QuestionnaireSchema({})
    validator = BlockValidator({"id": "confirm-name"}, questionnaire_schema)
    validator.questionnaire_schema.answers_with_context = {
        "name-answer": {
            "answer": {"id": "name-answer", "type": "TextField"},
            "block": "name",
        },
        "confirm-name-answer": {
            "answer": {"id": "confirm-name-answer"},
            "block": "confirm-name",
        },
    }
    validator.validate_source_references(
        [{"identifier": "name-answer", "source": "answers", "selector": "line1"}]
    )

    expected_errors = [
        {
            "message": BlockValidator.COMPOSITE_ANSWER_INVALID,
            "referenced_id": "name-answer",
            "block_id": "confirm-name",
        }
    ]
    assert validator.errors == expected_errors


def test_invalid_composite_answer_field_in_selector():
    questionnaire_schema = QuestionnaireSchema({})

    validator = BlockValidator({"id": "confirm-address"}, questionnaire_schema)
    validator.questionnaire_schema.answers_with_context = {
        "address-answer": {
            "answer": {"id": "address-answer", "type": "Address"},
            "block": "name",
        },
        "confirm-address-answer": {
            "answer": {"id": "confirm-address-answer"},
            "block": "confirm-address",
        },
    }
    validator.validate_source_references(
        [
            {
                "identifier": "address-answer",
                "source": "answers",
                "selector": "invalid-field",
            }
        ]
    )

    expected_errors = [
        {
            "message": BlockValidator.COMPOSITE_ANSWER_FIELD_INVALID,
            "referenced_id": "address-answer",
            "block_id": "confirm-address",
        }
    ]
    assert validator.errors == expected_errors


def test_invalid_placeholder_list_reference():
    filename = "schemas/invalid/test_invalid_placeholder_plurals.json"

    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("block1"), questionnaire_schema
    )
    validator.validate_list_source_reference(["people"])

    expected_errors = [
        {
            "message": BlockValidator.LIST_REFERENCE_INVALID,
            "block_id": "block1",
            "id": "people",
        }
    ]

    assert expected_errors == validator.errors


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


def test_invalid_use_of_relationship_id():
    filename = "schemas/invalid/test_invalid_use_of_relationship_id.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = BlockValidator(
        questionnaire_schema.get_block("relationships"), questionnaire_schema
    )

    expected_error_messages = [
        {"message": validator.RELATIONSHIPS_ID_USE_INVALID, "block_id": "relationships"}
    ]

    validator.validate()

    assert expected_error_messages == validator.errors
