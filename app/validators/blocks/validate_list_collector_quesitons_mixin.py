from app.validators.validator import Validator


def _options_contain_value(options, value):
    for option in options:
        if option["value"] == value:
            return True


class ValidateListCollectorQuestionsMixin(Validator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_collector_questions(
        self,
        collector_questions,
        answer_value,
        missing_radio_error,
        missing_value_error,
    ):
        for collector_question in collector_questions:
            for collector_answer in collector_question["answers"]:
                if collector_answer["type"] != "Radio":
                    self.add_error(missing_radio_error)

                if not _options_contain_value(
                    collector_answer["options"], answer_value
                ):
                    self.add_error(missing_value_error)
