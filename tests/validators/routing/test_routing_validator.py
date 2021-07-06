from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.routing_validator import RoutingValidator


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
    validator = RoutingValidator({}, {}, questionnaire_schema)

    validator.validate_routing_rules_have_default(rules, "conditional-routing-block")

    expected_error = {
        "message": validator.ROUTE_MUST_CONTAIN_DEFAULT,
        "block_or_group_id": "conditional-routing-block",
    }

    assert validator.errors[0] == expected_error


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
    validator = RoutingValidator({}, {}, questionnaire_schema)
    validator.validate_routing_rule_target([{"id": "mock-block"}], "block", rule)
    expected_error = {
        "message": validator.ROUTE_TARGET_INVALID,
        "goto_key": "block",
        "referenced_id": "invalid-location",
    }

    assert validator.errors == [expected_error]
