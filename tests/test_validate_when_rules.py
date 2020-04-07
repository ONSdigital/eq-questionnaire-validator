from app.validation import error_messages
from app.validation.questionnaire_validator import QuestionnaireValidator


def test_validate_answer_value_in_when_rule_invalid():
    when_rule = {"id": "answer-1", "condition": "equals", "value": "Yes"}
    option_value_to_answer_id_map = {
        "answer-1": {"Maybe", "No"},
        "answer-2": {"Yes", "No"},
    }

    validator = QuestionnaireValidator()
    validator.answer_id_to_option_values_map = option_value_to_answer_id_map

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

    validator = QuestionnaireValidator()
    validator.answer_id_to_option_values_map = option_value_to_answer_id_map

    validator.validate_answer_value_in_when_rule(when_rule)

    assert not validator.errors
