from app import error_messages
from app.validators.questionnaire_schema import get_routing_when_list, has_default_route
from app.validators.validator import Validator


class AnswerRoutingValidator(Validator):
    def __init__(self, answer, routing_rules):
        super(AnswerRoutingValidator, self).__init__(answer)
        self.answer = answer
        self.routing_rules = routing_rules
        self.default_route = has_default_route(routing_rules)

    def validate(self):
        self.validate_default_route()
        self.validate_routing_on_answer_options()

    def validate_default_route(self):
        if self.answer["mandatory"] and not self.default_route:
            self.errors.append(
                error_messages.UNDEFINED_QUESTION_DEFAULT_ROUTE,
                answer_id=self.answer["id"],
            )

    def validate_routing_on_answer_options(self):
        answer_options = self.answer.get("options", [])
        option_values = [option["value"] for option in answer_options]
        routing_when_list = get_routing_when_list(self.routing_rules)

        if answer_options:
            for when_clause in routing_when_list:
                for when in when_clause.get("when", []):
                    if (
                        when
                        and when.get("id", "") == self.answer["id"]
                        and when.get("value", "") in option_values
                    ):
                        option_values.remove(when["value"])
                    else:
                        option_values = []

            has_unrouted_options = option_values and len(option_values) != len(
                answer_options
            )

            if has_unrouted_options and not self.default_route:
                self.errors.append(
                    error_messages.UNDEFINED_ANSWER_ROUTING_RULE,
                    answer_id=self.answer["id"],
                    option_values=option_values,
                )
