from app.validators.validator import Validator


class AnswerValidator(Validator):
    def __init__(self, schema_element, questionnaire_schema=None):
        super().__init__(schema_element)
        self.answer = schema_element
        self.context["answer_id"] = self.answer["id"]
        if questionnaire_schema:
            self.questionnaire_schema = questionnaire_schema
