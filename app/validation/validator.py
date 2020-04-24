from abc import ABC


class Validator(ABC):
    def __init__(self, schema_element=None):
        self.errors = []
        self.schema_element = {} if schema_element is None else schema_element

    def add_error(self, message, **context):
        if "id" in self.schema_element:
            context["id"] = self.schema_element["id"]

        self.errors.append({"message": message, **context})

    def validate(self):
        pass
