from app import error_messages
from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.routing_validator import RoutingValidator
from tests.test_questionnaire_validator import _open_and_load_schema_file


def test_invalid_routing_default_block():
    rules = [
        {
            "goto": {
                "block": "response-yes",
                "when": [
                    {
                        "condition": "equals",
                        "id": "conditional-routing-answer",
                        "value": "Yes",
                    }
                ],
            }
        },
        {
            "goto": {
                "block": "invalid-location",
                "when": [
                    {
                        "condition": "equals",
                        "id": "conditional-routing-answer",
                        "value": "No, I prefer tea",
                    }
                ],
            }
        },
    ]
    questionnaire_schema = QuestionnaireSchema({})
    questionnaire_validator = RoutingValidator({}, {}, questionnaire_schema)

    questionnaire_validator.validate_routing_rules_have_default(
        rules, "conditional-routing-block"
    )

    expected_error = {
        "message": error_messages.ROUTE_MUST_CONTAIN_DEFAULT,
        "block_or_group_id": "conditional-routing-block",
    }

    assert questionnaire_validator.errors[0] == expected_error


def test_invalid_routing_block_id():

    rule = {
        "goto": {
            "block": "invalid-location",
            "when": [
                {
                    "condition": "equals",
                    "id": "conditional-routing-answer",
                    "value": "No, I prefer tea",
                }
            ],
        }
    }
    questionnaire_schema = QuestionnaireSchema({})
    routing_validator = RoutingValidator({}, {}, questionnaire_schema)
    routing_validator.validate_routing_rule_target(
        [{"id": "mock-block"}], "block", rule
    )
    expected_error = {
        "message": error_messages.ROUTE_TARGET_INVALID,
        "goto_key": "block",
        "referenced_id": "invalid-location",
    }

    assert routing_validator.errors == [expected_error]


def test_answer_comparisons_different_types():
    """ Ensures that when answer comparison is used, the type of the variables must be the same """
    filename = "schemas/invalid/test_invalid_answer_comparison_types.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    group = questionnaire_schema.get_group("route-group")
    block = questionnaire_schema.get_block("route-comparison-2")
    validator = RoutingValidator(block, group, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
            "comparison_id": "route-comparison-1-answer",
            "answer_id": "route-comparison-2-answer",
            "referenced_id": "route-comparison-2",
        },
        {
            "message": error_messages.NON_CHECKBOX_COMPARISON_ID,
            "comparison_id": "route-comparison-2-answer",
            "condition": "equals any",
        },
    ]

    assert expected_errors == validator.errors


def test_answer_comparisons_different_types_skip_group():
    """ Ensures that when answer comparison is used, the type of the variables must be the same """
    filename = "schemas/invalid/test_invalid_answer_comparison_types.json"
    questionnaire_schema = QuestionnaireSchema(_open_and_load_schema_file(filename))
    group = questionnaire_schema.get_group("skip-group")
    block = questionnaire_schema.get_block("less-than-answers")
    validator = RoutingValidator(block, group, questionnaire_schema)
    validator.validate()

    expected_errors = [
        {
            "message": error_messages.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
            "comparison_id": "comparison-2-answer",
            "answer_id": "comparison-1-answer",
            "referenced_id": "less-than-answers",
        },
        {
            "message": error_messages.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
            "comparison_id": "comparison-2-answer",
            "answer_id": "comparison-1-answer",
            "referenced_id": "less-than-answers",
        },
    ]

    assert validator.errors == expected_errors
