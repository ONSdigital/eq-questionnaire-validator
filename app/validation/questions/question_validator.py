from app.validation.validator import Validator


class QuestionValidator(Validator):
    question = {}

    def __init__(self, schema_element):
        super().__init__(schema_element)
        self.question = schema_element
        self.context["question_id"] = schema_element["id"]
