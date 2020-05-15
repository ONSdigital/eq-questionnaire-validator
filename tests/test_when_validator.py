from app import error_messages
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.when_validator import WhenValidator
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_validate_answer_value_in_when_rule_invalid():
    when_rule = {"id": "answer-1", "condition": "equals", "value": "Yes"}
    option_value_to_answer_id_map = {
        "answer-1": {"Maybe", "No"},
        "answer-2": {"Yes", "No"},
    }
    questionnaire_schema = QuestionnaireSchema({})
    validator = WhenValidator(when_rule, {}, questionnaire_schema)
    validator.questionnaire_schema.answer_id_to_option_values_map = (
        option_value_to_answer_id_map
    )

    validator.validate_answer_value_in_when_rule(when_rule)

    assert validator.errors[0] == {
        "message": error_messages.INVALID_WHEN_RULE_ANSWER_VALUE,
        "answer_id": "answer-1",
        "value": "Yes",
    }


def test_validate_answer_value_in_when_rule_valid():
    when_rule = {"id": "answer-1", "condition": "equals", "value": "Yes"}
    option_value_to_answer_id_map = {
        "answer-1": {"Yes", "No"},
        "answer-2": {"Yes", "No"},
    }

    questionnaire_schema = QuestionnaireSchema({})
    validator = WhenValidator(when_rule, {}, questionnaire_schema)
    validator.questionnaire_schema.answer_id_to_option_values_map = (
        option_value_to_answer_id_map
    )

    validator.validate_answer_value_in_when_rule(when_rule)

    assert not validator.errors


def test_invalid_answer_value_in_when_rule():
    filename = "schemas/invalid/test_invalid_answer_value_in_when_rule.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = WhenValidator({}, {}, questionnaire_schema)

    when = {
        "id": "country-checkbox-answer",
        "condition": "contains any",
        "values": ["France", 7, "Italian"],
    }
    expected_error_messages = [
        {
            "message": error_messages.INVALID_WHEN_RULE_ANSWER_VALUE,
            "answer_id": "country-checkbox-answer",
            "value": value,
        }
        for value in ["France", 7, "Italian"]
    ]

    validator.validate_answer_value_in_when_rule(when)

    assert validator.errors == expected_error_messages
