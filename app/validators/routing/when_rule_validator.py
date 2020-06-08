from app.validators.validator import Validator


class WhenRuleValidator(Validator):
    LIST_REFERENCE_INVALID = "Invalid list reference"
    CHECKBOX_MUST_USE_CORRECT_CONDITION = (
        "The condition cannot be used with `Checkbox` answer type"
    )
    CHECKBOX_CONDITION_ONLY = (
        "This condition can only be used with `Checkbox` answer types"
    )
    NON_CHECKBOX_COMPARISON_ID = (
        "The comparison_id is not for a Checkbox. The condition can only reference "
        "Checkbox answers when using comparison_id"
    )
    NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES = (
        "The answers used as comparison id and answer id in the `when` clause have "
        "different types"
    )
    INVALID_WHEN_RULE_ANSWER_VALUE = "Answer value in when rule has an invalid value"
    NON_EXISTENT_WHEN_KEY = (
        'The answer id in the key of the "when" clause does not exist'
    )

    def __init__(self, when_clause, referenced_id, questionnaire_schema):
        super().__init__(when_clause)
        self.when_clause = when_clause
        self.referenced_id = referenced_id
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        """
        Validates any answer id in a when clause exists within the schema
        Will also check that comparison exists
        """
        for when_rule in self.when_clause:
            if "list" in when_rule:
                self.validate_list_name_in_when_rule(when_rule)
                break

            valid_answer_ids = self.validate_answer_ids_present_in_schema(
                when_rule, self.referenced_id
            )
            if not valid_answer_ids:
                break

            # We know the ids are correct, so can continue to perform validation
            self.validate_checkbox_exclusive_conditions_in_when_rule(when_rule)

            if "comparison" in when_rule:
                self.validate_comparison_in_when_rule(when_rule, self.referenced_id)

            if "id" in when_rule:
                self.validate_answer_value_in_when_rule(when_rule)
        return self.errors

    def validate_checkbox_exclusive_conditions_in_when_rule(self, when):
        """
        Validate checkbox exclusive conditions are only used when answer type is Checkbox
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        condition = when["condition"]
        checkbox_exclusive_conditions = (
            "contains any",
            "contains all",
            "contains",
            "not contains",
        )
        all_checkbox_conditions = checkbox_exclusive_conditions + ("set", "not set")
        answer_type = (
            self.questionnaire_schema.answers_with_context[when["id"]]["answer"]["type"]
            if "id" in when
            else None
        )

        if answer_type == "Checkbox":
            if condition not in all_checkbox_conditions:
                answer_id = self.questionnaire_schema.answers_with_context[when["id"]][
                    "answer"
                ]["id"]
                self.add_error(
                    self.CHECKBOX_MUST_USE_CORRECT_CONDITION,
                    condition=condition,
                    answer_id=answer_id,
                )
        elif condition in checkbox_exclusive_conditions:
            answer_id = self.questionnaire_schema.answers_with_context[when["id"]][
                "answer"
            ]["id"]
            self.add_error(
                self.CHECKBOX_CONDITION_ONLY,
                condition=condition,
                answer_type=answer_type,
                answer_id=answer_id,
            )

    def validate_comparison_in_when_rule(self, when, referenced_id):
        """
        Validate that conditions requiring list match values define a comparison answer id that is of type Checkbox
        and ensure all other conditions with comparison id match answer types
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        if when["comparison"]["source"] == "answers":
            answer_id, comparison_id, condition = (
                when["id"],
                when["comparison"]["id"],
                when["condition"],
            )
            comparison_answer_type = self.questionnaire_schema.answers_with_context[
                comparison_id
            ]["answer"]["type"]
            id_answer_type = self.questionnaire_schema.answers_with_context[answer_id][
                "answer"
            ]["type"]
            conditions_requiring_list_match_values = (
                "equals any",
                "not equals any",
                "contains any",
                "contains all",
            )

            if condition in conditions_requiring_list_match_values:
                if comparison_answer_type != "Checkbox":
                    self.add_error(
                        self.NON_CHECKBOX_COMPARISON_ID,
                        comparison_id=comparison_id,
                        condition=condition,
                    )

            elif comparison_answer_type != id_answer_type:
                self.add_error(
                    self.NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES,
                    comparison_id=comparison_id,
                    answer_id=answer_id,
                    referenced_id=referenced_id,
                )

    def validate_answer_value_in_when_rule(self, when_rule):
        when_values = when_rule.get("values", [])
        when_value = when_rule.get("value")
        if when_value:
            when_values.append(when_value)

        option_values = self.questionnaire_schema.answer_id_to_option_values_map.get(
            when_rule["id"]
        )
        if not option_values:
            return []

        for value in when_values:
            if value not in option_values:
                self.add_error(
                    self.INVALID_WHEN_RULE_ANSWER_VALUE,
                    answer_id=when_rule["id"],
                    value=value,
                )

    def validate_answer_ids_present_in_schema(self, when, referenced_id):
        """
        Validates that any ids that are referenced within the when rule are present within the schema.  This prevents
        writing when conditions against id's that don't exist.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        ids_to_check = []

        if "id" in when:
            ids_to_check.append(("id", when["id"]))
        if "comparison" in when and when["comparison"]["source"] == "answers":
            ids_to_check.append(("comparison.id", when["comparison"]["id"]))

        for key, present_id in ids_to_check:
            if present_id not in self.questionnaire_schema.answers_with_context:
                self.add_error(
                    self.NON_EXISTENT_WHEN_KEY,
                    answer_id=present_id,
                    key=key,
                    referenced_id=referenced_id,
                )
                return False
        return True

    def validate_list_name_in_when_rule(self, when):
        """
        Validate that the list referenced in the when rule is defined in the schema
        """
        list_name = when["list"]
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(self.LIST_REFERENCE_INVALID, list_name=list_name)
