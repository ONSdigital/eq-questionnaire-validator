"""This code defines a base class for validators in a questionnaire validation system."""

from abc import ABC
from typing import Mapping


class Validator(ABC):
    """Base class for all validators."""

    def __init__(self, schema_element: Mapping | None = None):
        """Initializes the validator with an optional schema element."""
        self.errors = []
        self.context = {}
        self.schema_element = schema_element or {}

    def add_error(self, message, **context):
        """Adds an error message to the validator's error list."""
        self.errors.append({"message": message, **context, **self.context})

    def validate(self) -> list[dict]:
        """Validates the schema element and returns a list of errors found."""
        return self.errors
