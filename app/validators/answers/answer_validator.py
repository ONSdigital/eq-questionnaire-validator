from app.validators.validator import Validator


class AnswerValidator(Validator):
    def __init__(self, schema_element):
        super().__init__(schema_element)
        self.answer = schema_element
        self.answer_id = self.answer["id"]
        self.answer_type = self.answer["type"]
        self.context["answer_id"] = self.answer_id
