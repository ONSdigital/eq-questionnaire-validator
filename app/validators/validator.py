from abc import ABC
from typing import List


class Validator(ABC):
    def __init__(self, schema_element=None):
        self.errors = []
        self.context = {}
        self.schema_element = schema_element or {}

    def add_error(self, message, **context):
        self.errors.append({"message": message, **context, **self.context})

    def validate(self) -> List[dict]:
        return self.errors
