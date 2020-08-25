from app.validators.validator import Validator


def _options_contain_action_type(options, expected_action):
    return any(
        option["action"]["type"] == expected_action
        for option in options
        if "action" in option
    )


class ValidateListCollectorQuestionsMixin(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_collector_questions(
        self,
        collector_questions,
        missing_radio_error,
        expected_action,
        missing_action_error,
    ):
        for collector_question in collector_questions:
            for collector_answer in collector_question["answers"]:
                if collector_answer["type"] != "Radio":
                    self.add_error(missing_radio_error)

                if not _options_contain_action_type(
                    collector_answer["options"], expected_action
                ):
                    self.add_error(missing_action_error)
