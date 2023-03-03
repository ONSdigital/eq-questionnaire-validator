from app import error_messages
from app.answer_type import AnswerOptionType, AnswerType
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
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


class Operator:
    NOT = "not"
    AND = "and"
    OR = "or"
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    IN = "in"
    ALL_IN = "all-in"
    ANY_IN = "any-in"
    COUNT = "count"
    DATE = "date"
    FORMAT_DATE = "format-date"
    DATE_RANGE = "date-range"
    MAP = "map"
    OPTION_LABEL_FROM_VALUE = "option-label-from-value"
    CONCATENATE = "concatenate"
    SUM = "+"


LOGIC_OPERATORS = [Operator.NOT, Operator.AND, Operator.OR]

COMPARISON_OPERATORS = [
    Operator.EQUAL,
    Operator.NOT_EQUAL,
    Operator.GREATER_THAN,
    Operator.LESS_THAN,
    Operator.GREATER_THAN_OR_EQUAL,
    Operator.LESS_THAN_OR_EQUAL,
]

ARRAY_OPERATORS = [Operator.IN, Operator.ALL_IN, Operator.ANY_IN]

VALUE_OPERATORS = [
    Operator.DATE,
    Operator.COUNT,
    Operator.FORMAT_DATE,
    Operator.DATE_RANGE,
    Operator.MAP,
]

NUMERIC_OPERATORS = [Operator.SUM, Operator.COUNT]

ALL_OPERATORS = (
    LOGIC_OPERATORS
    + COMPARISON_OPERATORS
    + ARRAY_OPERATORS
    + VALUE_OPERATORS
    + NUMERIC_OPERATORS
)

ALL_WHEN_RULE_OPERATORS = (
    LOGIC_OPERATORS
    + COMPARISON_OPERATORS
    + ARRAY_OPERATORS
    + [Operator.DATE, Operator.COUNT]
)

SELF_REFERENCE_KEY = "self"


class RulesValidator(Validator):
    VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS = "Value doesn't exist in answer options"
    DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER = (
        "Date operator references non Date, MonthYearDate, or YearDate answer"
    )
    COUNT_OPERATOR_REFERENCES_NON_CHECKBOX_ANSWER = (
        "Count operator references non Checkbox answer"
    )
    MAP_OPERATOR_WITHOUT_SELF_REFERENCE = (
        f"Argument one of the `map` operator does not reference `{SELF_REFERENCE_KEY}`"
    )
    SELF_REFERENCE_OUTSIDE_MAP_OPERATOR = (
        f"Reference to {SELF_REFERENCE_KEY} was made outside of the `map` operator"
    )
    ANSWER_TYPE_FOR_SUM_OPERATOR_INVALID = "Expected the answer type for sum operator to be type 'number' but got type '{answer_type}'"
    OPERATOR_ARGUMENT_TYPE_MISMATCH = "Argument types don't match"
    INVALID_ARGUMENT_TYPE_FOR_OPERATOR = "Invalid argument type for operator"

    def __init__(
        self, rules, origin_id, questionnaire_schema, *, allow_self_reference=False
    ):
        super().__init__(rules)
        self.rules = rules
        self.questionnaire_schema = questionnaire_schema
        self.context["origin_id"] = origin_id
        self.allow_self_reference = allow_self_reference

    def validate(self):
        """
        Validate that the top level rules are valid
        """
        self._validate_rule(self.rules, allow_self_reference=self.allow_self_reference)
        self._validate_operator_arguments(self.rules)
        return self.errors

    def _validate_rule(self, rules, *, allow_self_reference):
        operator_name = next(iter(rules))
        allow_self_reference = allow_self_reference or operator_name == Operator.MAP

        arguments = rules[operator_name]
        for argument in arguments:
            if isinstance(argument, dict) and any(
                operator in argument for operator in ALL_OPERATORS
            ):
                self._validate_rule(argument, allow_self_reference=allow_self_reference)

        if operator_name == Operator.DATE:
            self._validate_date_operator(rules)

        elif operator_name == Operator.MAP:
            self._validate_map_operator(rules)

        elif operator_name == Operator.OPTION_LABEL_FROM_VALUE:
            self._validate_option_label_from_value_operator(rules)

        if operator_name in [Operator.FORMAT_DATE, Operator.DATE]:
            self._validate_self_references(
                rules, operator_name, allow_self_reference=allow_self_reference
            )

        self._validate_options(rules, operator_name)

    def _validate_self_references(self, rules, operator_name, *, allow_self_reference):
        """
        Validate references to `self` are within the context of the `map` operator
        """
        arguments_for_non_map_operators = (
            self._get_flattened_arguments_for_non_map_operators(rules[operator_name])
        )
        if (
            SELF_REFERENCE_KEY in arguments_for_non_map_operators
            and not allow_self_reference
        ):
            self.add_error(self.SELF_REFERENCE_OUTSIDE_MAP_OPERATOR, rule=rules)

    def _validate_map_operator(self, operator):
        """
        Validates that the first argument to the map operator has a reference to `self`
        The second argument is currently not validated here as it can currently only be `date-range`
        """
        function_to_map_over_arguments = list(operator["map"][0].values())[0]
        if SELF_REFERENCE_KEY in function_to_map_over_arguments:
            return None

        arguments_for_non_map_operators = (
            self._get_flattened_arguments_for_non_map_operators(
                function_to_map_over_arguments
            )
        )

        if SELF_REFERENCE_KEY not in arguments_for_non_map_operators:
            self.add_error(
                self.MAP_OPERATOR_WITHOUT_SELF_REFERENCE, rule=operator["map"][0]
            )

    def _get_flattened_arguments_for_non_map_operators(self, arguments):
        """
        Recursively fetch all the arguments for all non `map` operators as a flattened list.

        The `map` operator is checked explicitly.
        """
        return [
            non_operator_argument
            for argument in arguments
            for non_operator_argument in self._get_non_map_arguments_from_argument(
                argument
            )
        ]

    def _get_non_map_arguments_from_argument(self, argument):
        """
        For the given argument, recursively fetch all the arguments for all non `map` operators as a flattened list.

        The `map` operator is checked explicitly.
        """

        non_operator_arguments = []
        if isinstance(argument, dict) and any(
            operator in argument
            for operator in ALL_OPERATORS
            if operator != Operator.MAP
        ):
            for operands in argument.values():
                non_operator_arguments += (
                    self._get_flattened_arguments_for_non_map_operators(operands)
                )
        else:
            non_operator_arguments.append(argument)

        return non_operator_arguments

    def _validate_option_label_from_value_operator(self, operator):
        """
        Validate the referenced answer id in `option-label-from-value` exists
        and is of type ['Radio','Checkbox','Dropdown']
        """
        answer_id = operator[next(iter(operator))][1]
        answers = self.questionnaire_schema.answers_with_context
        if answer_id not in answers:
            self.add_error(
                ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
                identifier=answer_id,
            )

        elif not any(
            x.value == answers[answer_id]["answer"]["type"] for x in AnswerOptionType
        ):
            self.add_error(
                error_messages.ANSWER_TYPE_FOR_OPTION_LABEL_FROM_VALUE_INVALID,
                identifier=answer_id,
            )

    def _validate_date_operator(self, operator):
        """
        Validates that when an answer value source is used, it is a date
        """
        first_argument = operator["date"][0]
        if (
            isinstance(first_argument, dict)
            and first_argument.get("source") == "answers"
            and self.questionnaire_schema.get_answer_type(first_argument["identifier"])
            not in [AnswerType.DATE, AnswerType.MONTH_YEAR_DATE, AnswerType.YEAR_DATE]
        ):
            self.add_error(
                self.DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER,
                value_source=first_argument,
            )

    def _validate_options(self, rules, operator_name):
        """
        Validates that answer options referenced in a rule exist
        """
        values = []
        option_values = []
        for argument in rules[operator_name]:
            if isinstance(argument, dict) and argument.get("source") == "answers":
                option_values = (
                    self.questionnaire_schema.answer_id_to_option_values_map.get(
                        argument["identifier"]
                    )
                )
            else:
                values = argument if isinstance(argument, list) else [argument]

        if values and option_values:
            for value in values:
                # Null values are allowed and will not exist in answer options
                if value and value not in option_values:
                    self.add_error(
                        self.VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS,
                        value=value,
                        answer_options=list(option_values),
                    )

    def _validate_operator_arguments(self, rule):
        operator_name = next(iter(rule))
        argument_types = self._get_argument_types_for_operator(rule[operator_name])

        if operator_name in COMPARISON_OPERATORS + ARRAY_OPERATORS + NUMERIC_OPERATORS:
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

        if operator_name in NUMERIC_OPERATORS:
            return TYPE_NUMBER

        return TYPE_BOOLEAN

    def _get_argument_types_for_operator(self, arguments):
        argument_types = []
        for argument in arguments:
            if isinstance(argument, dict) and any(
                operator in argument for operator in ALL_WHEN_RULE_OPERATORS
            ):
                argument_type = self._validate_operator_arguments(argument)
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
            return (
                [TYPE_NUMBER, TYPE_STRING] if argument_position == 0 else [TYPE_ARRAY]
            )
        if operator_name == Operator.COUNT:
            return [TYPE_ARRAY]

        if operator_name == Operator.SUM:
            return [TYPE_NUMBER]
