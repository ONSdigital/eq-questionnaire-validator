from abc import ABC


class Validator(ABC):
    def __init__(self, schema_element=None):
        self.errors = []
        self.context = {}
        self.schema_element = {} if schema_element is None else schema_element

    def add_error(self, message, **context):
        self.errors.append({"message": message, **context, **self.context})

    def validate(self):
        pass
