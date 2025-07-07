"""Tests for the RoutingValidator class."""

from app.validators.questionnaire_schema import QuestionnaireSchema
from app.validators.routing.routing_validator import RoutingValidator


def get_validator(routing_rules, origin_id):
    """Creates a RoutingValidator instance with the given routing rules and origin ID."""
    return RoutingValidator(
        routing_rules=routing_rules,
        group={},
        origin_id=origin_id,
        questionnaire_schema=QuestionnaireSchema({}),
    )


def test_route_must_contain_default():
    """Tests that a routing rule without a default case raises an error."""
    routing_rules = [
        {
            "block": "response-yes",
            "when": {"==": [{"source": "answers", "identifier": "answer-1"}, "Yes"]},
        },
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rules_has_single_default_rule(routing_rules)

    expected_error = {
        "message": validator.ROUTING_RULES_DO_NOT_HAVE_A_DEFAULT_RULE,
        "origin_id": "block-id",
    }

    assert validator.errors == [expected_error]


def test_route_has_too_many_defaults():
    """Tests that a routing rule with too many default cases raises an error."""
    routing_rules = [{"block": "response-yes"}, {"block": "response-no"}]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rules_has_single_default_rule(routing_rules)

    expected_error = {
        "message": validator.ROUTING_RULES_HAS_TOO_MANY_DEFAULTS,
        "origin_id": "block-id",
    }

    assert validator.errors == [expected_error]


def test_invalid_destination_block_id():
    """Tests that a routing rule with an invalid block ID raises an error."""
    routing_rules = [
        {
            "block": "non-existent-block-id",
            "when": {
                "==": [
                    {"source": "answers", "identifier": "conditional-routing-answer"},
                    "Yes",
                ],
            },
        },
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="block-id")
    validator.validate_routing_rule_block_target(
        rule=routing_rules[0], block_ids=["mock-block-id"],
    )

    expected_error = {
        "message": validator.ROUTING_RULE_BLOCK_TARGET_INVALID,
        "origin_id": "block-id",
        "destination_id": "non-existent-block-id",
    }

    assert validator.errors == [expected_error]


def test_invalid_destination_group_id():
    """Tests that a routing rule with an invalid group ID raises an error."""
    routing_rules = [
        {
            "group": "non-existent-group-id",
            "when": {
                "==": [
                    {"source": "answers", "identifier": "conditional-routing-answer"},
                    "Yes",
                ],
            },
        },
    ]

    validator = get_validator(routing_rules=routing_rules, origin_id="group-id")
    validator.validate_routing_rule_group_target(
        rule=routing_rules[0], group_ids=["mock-group-id"],
    )

    expected_error = {
        "message": validator.ROUTING_RULE_GROUP_TARGET_INVALID,
        "origin_id": "group-id",
        "destination_id": "non-existent-group-id",
    }

    assert validator.errors == [expected_error]
