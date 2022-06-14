from app.validators.routing.types import (
    TYPE_ARRAY,
    TYPE_BOOLEAN,
    TYPE_DATE,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_STRING,
    python_type_to_json_type,
    resolve_value_source_json_type,
)
from app.validators.rules.rule_validator import (
    ARRAY_OPERATORS,
    COMPARISON_OPERATORS,
    LOGIC_OPERATORS,
    Operator,
    RulesValidator,
)

ALL_WHEN_RULE_OPERATORS = (
    LOGIC_OPERATORS
    + COMPARISON_OPERATORS
    + ARRAY_OPERATORS
    + [Operator.DATE, Operator.COUNT]
)


class NewWhenRuleValidator(RulesValidator):
    OPERATOR_ARGUMENT_TYPE_MISMATCH = "Argument types don't match"
    INVALID_ARGUMENT_TYPE_FOR_OPERATOR = "Invalid argument type for operator"

    def validate(self):
        """
        Validates all operators and arguments in when clause
        """
        super().validate()
        self.validate_rule(self.rules)

        return self.errors

    def validate_rule(self, rule):
        operator_name = next(iter(rule))
        argument_types = self._get_argument_types_for_operator(rule[operator_name])

        if operator_name in COMPARISON_OPERATORS + ARRAY_OPERATORS:
            self._validate_comparison_operator_argument_types(
                rule, operator_name, argument_types
            )

        if (
            operator_name in COMPARISON_OPERATORS + [Operator.ALL_IN, Operator.ANY_IN]
            and TYPE_NULL not in argument_types
        ):
            self._validate_argument_types_match(rule, argument_types)

        if operator_name == Operator.DATE:
            return TYPE_DATE

        if operator_name == Operator.COUNT:
            return TYPE_NUMBER

        return TYPE_BOOLEAN

    def _get_argument_types_for_operator(self, arguments):
        argument_types = []
        for argument in arguments:
            if isinstance(argument, dict) and any(
                operator in argument for operator in ALL_WHEN_RULE_OPERATORS
            ):
                argument_type = self.validate_rule(argument)
            elif isinstance(argument, dict) and "source" in argument:
                argument_type = resolve_value_source_json_type(
                    argument, self.questionnaire_schema
                )
            else:
                argument_type = python_type_to_json_type(type(argument).__name__)

            argument_types.append(argument_type)

        return argument_types

    def _validate_argument_types_match(self, rule, argument_types):
        """
        Validates that all arguments are of the same type
        """
        if len(set(argument_types)) > 1:
            self.add_error(
                self.OPERATOR_ARGUMENT_TYPE_MISMATCH,
                rule=str(rule),
                argument_types=argument_types,
            )

    def _validate_comparison_operator_argument_types(
        self, rule, operator_name, argument_types
    ):
        """
        Validates that all arguments are of the correct type for the operator
        """
        for argument_position, _ in enumerate(rule[operator_name]):
            valid_types = self._get_valid_types_for_operator(
                operator_name, argument_position=argument_position
            )
            if argument_types[argument_position] not in valid_types:
                self.add_error(
                    self.INVALID_ARGUMENT_TYPE_FOR_OPERATOR,
                    argument_value=rule[operator_name][argument_position],
                    argument_type=argument_types[argument_position],
                    operator=operator_name,
                    valid_types=valid_types,
                )

    @staticmethod
    def _get_valid_types_for_operator(operator_name, argument_position):
        if operator_name in [Operator.EQUAL, Operator.NOT_EQUAL]:
            return [TYPE_DATE, TYPE_NUMBER, TYPE_STRING, TYPE_NULL, TYPE_ARRAY]

        if operator_name in [
            Operator.LESS_THAN,
            Operator.LESS_THAN_OR_EQUAL,
            Operator.GREATER_THAN,
            Operator.GREATER_THAN_OR_EQUAL,
        ]:
            return [TYPE_DATE, TYPE_NUMBER]

        if operator_name in [Operator.ANY_IN, Operator.ALL_IN]:
            return [TYPE_ARRAY]

        if operator_name == Operator.IN:
            if argument_position == 0:
                return [TYPE_NUMBER, TYPE_STRING]
            return [TYPE_ARRAY]
