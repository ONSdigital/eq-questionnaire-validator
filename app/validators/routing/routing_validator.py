"""This module contains the RoutingValidator class, which validates routing rules within a questionnaire schema.

Classes:
    RoutingValidator
"""

from app.validators.rules.rule_validator import RulesValidator
from app.validators.validator import Validator


class RoutingValidator(Validator):
    """Validator for routing rules in a questionnaire schema.

    Attributes:
        routing_rules (list): The list of routing rules to be validated.
        group (dict): The group containing the routing rules, used for validating block targets.
        origin_id (str): The identifier of the element from which the routing rules originate, used for error reporting.
        questionnaire_schema (QuestionnaireSchema): The entire questionnaire schema, used for validating group targets
        and rule conditions.

    Methods:
        validate
        validate_routing_rules_has_single_default_rule
        validate_routing_rule_block_target
        validate_routing_rule_group_target
        validate_routing_rule
    """

    ROUTING_RULES_DO_NOT_HAVE_A_DEFAULT_RULE = "Routing rules do not have a default rule"
    ROUTING_RULES_HAS_TOO_MANY_DEFAULTS = "Routing rules have more than one default rule"
    ROUTING_RULE_BLOCK_TARGET_INVALID = "Routing rule routes to invalid block"
    ROUTING_RULE_GROUP_TARGET_INVALID = "Routing rule routes to invalid group"

    def __init__(self, routing_rules, group, origin_id, questionnaire_schema):
        super().__init__(routing_rules)
        self.routing_rules = routing_rules
        self.group = group
        self.origin_id = origin_id
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        """Validate the routing rules by calling multiple helper methods to check for the presence of a single default
        rule, validate block and group targets.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        self.validate_routing_rules_has_single_default_rule(self.routing_rules)

        block_ids = [block["id"] for block in self.group["blocks"]]

        for rule in self.routing_rules:
            if "block" in rule:
                self.validate_routing_rule_block_target(rule, block_ids)
            elif "group" in rule:
                self.validate_routing_rule_group_target(
                    rule,
                    self.questionnaire_schema.group_ids,
                )
            self.validate_routing_rule(rule)

        return self.errors

    def validate_routing_rules_has_single_default_rule(self, rules):
        """Ensure that a set of routing rules contains one default rule, without a when clause.

        Args:
            rules (list): A list of routing rules to be validated.
        """
        default_routing_rule_count = sum("when" not in rule for rule in rules)

        if not default_routing_rule_count:
            self.add_error(
                self.ROUTING_RULES_DO_NOT_HAVE_A_DEFAULT_RULE,
                origin_id=self.origin_id,
            )
        elif default_routing_rule_count > 1:
            self.add_error(
                self.ROUTING_RULES_HAS_TOO_MANY_DEFAULTS,
                origin_id=self.origin_id,
            )

    def validate_routing_rule_block_target(self, rule, block_ids):
        """Ensure that a routing rule that routes to a block has a valid block target.

        Args:
            rule (dict): The routing rule to be validated.
            block_ids (list): A list of block identifiers within the group.
        """
        destination_block_id = rule["block"]
        if destination_block_id not in block_ids:
            self.add_error(
                self.ROUTING_RULE_BLOCK_TARGET_INVALID,
                origin_id=self.origin_id,
                destination_id=destination_block_id,
            )

    def validate_routing_rule_group_target(self, rule, group_ids):
        """Ensure that a routing rule that routes to a group has a valid group target.

        Args:
            rule (dict): The routing rule to be validated.
            group_ids (list): A list of group identifiers within the questionnaire schema.
        """
        destination_group_id = rule["group"]
        if destination_group_id not in group_ids:
            self.add_error(
                self.ROUTING_RULE_GROUP_TARGET_INVALID,
                origin_id=self.origin_id,
                destination_id=destination_group_id,
            )

    def validate_routing_rule(self, rule):
        """Validate a routing rule by validating its "when" condition if it exists using the RulesValidator.

        Args:
            rule (dict): The routing rule to be validated.
        """
        if rule and "when" in rule:
            when_validator = RulesValidator(
                rule["when"],
                self.origin_id,
                self.questionnaire_schema,
            )
            self.errors += when_validator.validate()
