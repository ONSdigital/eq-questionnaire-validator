from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.new_routing_validator import NewRoutingValidator


def get_validator(routing_rules, origin_id):
    return NewRoutingValidator(
        routing_rules=routing_rules,
        group={},
        origin_id=origin_id,
        questionnaire_schema=QuestionnaireSchema({}),
    )


def test_route_must_contain_default():
    routing_rules = [
        {
            "block": "response-yes",
            "when": {"==": [{"source": "answers", "identifier": "answer-1"}, "Yes"]},
        }
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rules_has_single_default_rule(routing_rules)

    expected_error = {
        "message": validator.ROUTING_RULES_DO_NOT_HAVE_A_DEFAULT_RULE,
        "origin_id": "block-id",
    }

    assert validator.errors == [expected_error]


def test_route_has_too_many_defaults():
    routing_rules = [{"block": "response-yes"}, {"block": "response-no"}]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rules_has_single_default_rule(routing_rules)

    expected_error = {
        "message": validator.ROUTING_RULES_HAS_TOO_MANY_DEFAULTS,
        "origin_id": "block-id",
    }

    assert validator.errors == [expected_error]


def test_invalid_destination_block_id():
    routing_rules = [
        {
            "block": "non-existent-block-id",
            "when": {
                "==": [
                    {"source": "answers", "identifier": "conditional-routing-answer"},
                    "Yes",
                ]
            },
        }
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rule_block_target(
        rule=routing_rules[0], block_ids=["mock-block-id"]
    )

    expected_error = {
        "message": validator.ROUTING_RULE_BLOCK_TARGET_INVALID,
        "origin_id": "block-id",
        "destination_id": "non-existent-block-id",
    }

    assert validator.errors == [expected_error]


def test_invalid_destination_group_id():
    routing_rules = [
        {
            "group": "non-existent-group-id",
            "when": {
                "==": [
                    {"source": "answers", "identifier": "conditional-routing-answer"},
                    "Yes",
                ]
            },
        }
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="group-id")
    validator.validate_routing_rule_group_target(
        rule=routing_rules[0], group_ids=["mock-group-id"]
    )

    expected_error = {
        "message": validator.ROUTING_RULE_GROUP_TARGET_INVALID,
        "origin_id": "group-id",
        "destination_id": "non-existent-group-id",
    }

    assert validator.errors == [expected_error]
