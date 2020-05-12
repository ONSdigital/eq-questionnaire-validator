from app.validation.questionnaire_schema import QuestionnaireSchema
from app.validation.routing.routing_validator import RoutingValidator


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
        "message": "The routing rules for group or block: conditional-routing-block must contain a default routing "
        "rule without a when rule"
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

    expected_error = {
        "message": "Routing rule routes to invalid block [invalid-location]"
    }

    routing_validator.validate_routing_rule_target(
        [{"id": "a-valid-location"}], "block", rule
    )

    assert routing_validator.errors[0] == expected_error
