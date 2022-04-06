from app import error_messages
from app.answer_type import AnswerOptionType, AnswerType
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

ALL_OPERATORS = (
    LOGIC_OPERATORS + COMPARISON_OPERATORS + ARRAY_OPERATORS + VALUE_OPERATORS
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

        elif operator_name == Operator.COUNT:
            self._validate_count_operator(rules)

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

    def _validate_count_operator(self, operator):
        """
        Validates that an answer value source within a count operator is of type Checkbox
        """
        first_argument = operator["count"][0]
        if (
            isinstance(first_argument, dict)
            and first_argument.get("source") == "answers"
            and self.questionnaire_schema.get_answer_type(first_argument["identifier"])
            != AnswerType.CHECKBOX
        ):
            self.add_error(
                self.COUNT_OPERATOR_REFERENCES_NON_CHECKBOX_ANSWER,
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
