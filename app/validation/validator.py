from abc import ABC


class Validator(ABC):
    def __init__(self, schema_element):
        self.schema_element = schema_element
        self.errors = []

    def add_error(self, message, **context):
        if "id" in self.schema_element:
            context["id"] = self.schema_element["id"]

        self.errors.append({"message": message, **context})
