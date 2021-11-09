from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.when_rule_validator import WhenRuleValidator
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_validate_answer_value_in_when_rule_invalid():
    when_rule = {"id": "answer-1", "condition": "equals", "value": "Yes"}
    option_value_to_answer_id_map = {
        "answer-1": {"Maybe", "No"},
        "answer-2": {"Yes", "No"},
    }
    questionnaire_schema = QuestionnaireSchema({})
    validator = WhenRuleValidator(when_rule, {}, questionnaire_schema)
    validator.questionnaire_schema.answer_id_to_option_values_map = (
        option_value_to_answer_id_map
    )

    validator.validate_answer_value_in_when_rule(when_rule)

    assert validator.errors[0] == {
        "message": WhenRuleValidator.INVALID_WHEN_RULE_ANSWER_VALUE,
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
    validator = WhenRuleValidator(when_rule, {}, questionnaire_schema)
    validator.questionnaire_schema.answer_id_to_option_values_map = (
        option_value_to_answer_id_map
    )

    validator.validate_answer_value_in_when_rule(when_rule)

    assert not validator.errors


def test_invalid_answer_value_in_when_rule():
    filename = "schemas/invalid/test_invalid_answer_value_in_when_rule.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    validator = WhenRuleValidator({}, {}, questionnaire_schema)

    when = {
        "id": "country-checkbox-answer",
        "condition": "contains any",
        "values": ["France", 7, "Italian"],
    }
    expected_error_messages = [
        {
            "message": WhenRuleValidator.INVALID_WHEN_RULE_ANSWER_VALUE,
            "answer_id": "country-checkbox-answer",
            "value": value,
        }
        for value in ["France", 7, "Italian"]
    ]

    validator.validate_answer_value_in_when_rule(when)

    assert validator.errors == expected_error_messages


def test_answer_comparisons_different_types():
    """Ensures that when answer comparison is used, the type of the variables must be the same"""
    when_rule = {
        "id": "comparison-1-answer",
        "condition": "equals any",
        "comparison": {"id": "comparison-2-answer", "source": "answers"},
    }
    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "comparison-1-answer": {
            "answer": {"id": "comparison-1-answer", "type": "Number"},
            "block": "route-comparison-1",
        },
        "comparison-2-answer": {
            "answer": {"id": "comparison-2-answer", "type": "TextField"},
            "block": "comparison-2",
        },
    }
    validator = WhenRuleValidator(when_rule, {}, questionnaire_schema)
    validator.validate_comparison_in_when_rule(when_rule, "block-id")

    expected_errors = [
        {
            "message": WhenRuleValidator.NON_CHECKBOX_COMPARISON_ID,
            "comparison_id": "comparison-2-answer",
            "condition": "equals any",
        }
    ]

    assert expected_errors == validator.errors


def test_answer_comparisons_different_types_skip_group():
    """Ensures that when answer comparison is used, the type of the variables must be the same"""
    when_rule = {
        "id": "comparison-1-answer",
        "condition": "less than",
        "comparison": {"id": "comparison-2-answer", "source": "answers"},
    }
    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_schema.answers_with_context = {
        "comparison-1-answer": {
            "answer": {"id": "comparison-1-answer", "type": "Number"},
            "block": "route-comparison-1",
        },
        "comparison-2-answer": {
            "answer": {"id": "comparison-2-answer", "type": "TextField"},
            "block": "comparison-2",
        },
    }
    validator = WhenRuleValidator(when_rule, {}, questionnaire_schema)
    validator.validate_comparison_in_when_rule(when_rule, "block-id")

    expected_errors = [
        {
            "message": WhenRuleValidator.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
            "comparison_id": "comparison-2-answer",
            "answer_id": "comparison-1-answer",
            "referenced_id": "block-id",
        }
    ]

    assert expected_errors == validator.errors
