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

OPERATOR_NOT = "not"
OPERATOR_AND = "and"
OPERATOR_OR = "or"
OPERATOR_EQUAL = "=="
OPERATOR_NOT_EQUAL = "!="
OPERATOR_GREATER_THAN = ">"
OPERATOR_LESS_THAN = "<"
OPERATOR_GREATER_THAN_OR_EQUAL = ">="
OPERATOR_LESS_THAN_OR_EQUAL = "<="
OPERATOR_IN = "in"
OPERATOR_ALL_IN = "all-in"
OPERATOR_ANY_IN = "any-in"
OPERATOR_DATE = "date"

LOGIC_OPERATORS = [OPERATOR_NOT, OPERATOR_AND, OPERATOR_OR]

COMPARISON_OPERATORS = [
    OPERATOR_EQUAL,
    OPERATOR_NOT_EQUAL,
    OPERATOR_GREATER_THAN,
    OPERATOR_LESS_THAN,
    OPERATOR_GREATER_THAN_OR_EQUAL,
    OPERATOR_LESS_THAN_OR_EQUAL,
]

ARRAY_OPERATORS = [OPERATOR_IN, OPERATOR_ALL_IN, OPERATOR_ANY_IN]

VALUE_OPERATORS = [OPERATOR_DATE]

ALL_OPERATORS = (
    LOGIC_OPERATORS + COMPARISON_OPERATORS + ARRAY_OPERATORS + VALUE_OPERATORS
)


class NewWhenRuleValidator(Validator):
    OPERATOR_ARGUMENT_TYPE_MISMATCH = "Argument types don't match"
    INVALID_ARGUMENT_TYPE_FOR_OPERATOR = "Invalid argument type for operator"
    VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS = "Value doesn't exist in answer options"
    DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER = (
        "Date operator references non Date, MonthYearDate, or YearDate answer"
    )

    def __init__(self, when_clause, origin_id, questionnaire_schema):
        super().__init__(when_clause)
        self.when_clause = when_clause
        self.questionnaire_schema = questionnaire_schema
        self.context["origin_id"] = origin_id

    def validate(self):
        """
        Validates all operators and arguments in when clause
        """
        self.validate_rule(self.when_clause)

        return self.errors

    def validate_rule(self, rule):
        operator_name = next(iter(rule))
        argument_types = []
        for argument in rule[operator_name]:
            if isinstance(argument, dict) and any(
                operator in argument for operator in ALL_OPERATORS
            ):
                argument_type = self.validate_rule(argument)
            elif isinstance(argument, dict) and "source" in argument:
                argument_type = resolve_value_source_json_type(
                    argument, self.questionnaire_schema.answers_with_context
                )
            else:
                argument_type = python_type_to_json_type(type(argument).__name__)
            argument_types.append(argument_type)

        if operator_name == OPERATOR_DATE:
            self._validate_date_operator(rule)

        if operator_name in COMPARISON_OPERATORS + ARRAY_OPERATORS:
            self._validate_comparison_operator_argument_types(
                rule, operator_name, argument_types
            )

        if (
            operator_name in COMPARISON_OPERATORS + [OPERATOR_ALL_IN, OPERATOR_ANY_IN]
            and TYPE_NULL not in argument_types
        ):
            self._validate_argument_types_match(rule, argument_types)

        if operator_name in ARRAY_OPERATORS + [OPERATOR_EQUAL, OPERATOR_NOT_EQUAL]:
            self._validate_options(rule, operator_name)

        if operator_name == OPERATOR_DATE:
            return TYPE_DATE
        return TYPE_BOOLEAN

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

    def _validate_date_operator(self, operator):
        """
        Validates that when an answer value source is used it is a date
        """
        first_argument = operator["date"][0]
        if (
            isinstance(first_argument, dict)
            and first_argument.get("source") == "answers"
            and self.questionnaire_schema.get_answer(first_argument["identifier"])[
                "type"
            ]
            not in ["Date", "MonthYearDate", "YearDate"]
        ):
            self.add_error(
                self.DATE_OPERATOR_REFERENCES_NON_DATE_ANSWER,
                value_source=first_argument,
            )

    def _validate_options(self, rule, operator_name):
        """
        Validates that answer options referenced in a rule exist
        """
        values = []
        option_values = []
        for argument in rule[operator_name]:
            if isinstance(argument, dict) and argument.get("source") == "answers":
                option_values = self.questionnaire_schema.answer_id_to_option_values_map.get(
                    argument["identifier"]
                )
            else:
                values = argument if isinstance(argument, list) else [argument]

        if values and option_values:
            for value in values:
                if value not in option_values:
                    self.add_error(
                        self.VALUE_DOESNT_EXIST_IN_ANSWER_OPTIONS,
                        value=value,
                        answer_options=option_values,
                    )

    @staticmethod
    def _get_valid_types_for_operator(operator_name, argument_position):
        if operator_name in [OPERATOR_EQUAL, OPERATOR_NOT_EQUAL]:
            return [TYPE_DATE, TYPE_NUMBER, TYPE_STRING, TYPE_NULL]

        if operator_name in [
            OPERATOR_LESS_THAN,
            OPERATOR_LESS_THAN_OR_EQUAL,
            OPERATOR_GREATER_THAN,
            OPERATOR_GREATER_THAN_OR_EQUAL,
        ]:
            return [TYPE_DATE, TYPE_NUMBER]

        if operator_name in [OPERATOR_ANY_IN, OPERATOR_ALL_IN]:
            return [TYPE_ARRAY]

        if operator_name == OPERATOR_IN:
            if argument_position == 0:
                return [TYPE_NUMBER, TYPE_STRING]
            return [TYPE_ARRAY]
