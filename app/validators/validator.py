"""Defines the base class for all validators.

Classes:
    Validator
"""

from abc import ABC
from typing import Mapping


class Validator(ABC):
    """Base class for validators.

    All validators inherit from this class and implement the validate method to perform
    validation on a given schema element.

    Methods:
        add_error
        validate
    """

    def __init__(self, schema_element: Mapping | None = None):
        self.errors: list[dict] = []
        self.context: dict[str, str] = {}
        self.schema_element = schema_element or {}

    def add_error(self, message, **context):
        """Adds an error message to the list of errors with optional context.

        Args:
            message (str): The error message to add.
            **context (dict): Additional information to include with the error.
        """
        self.errors.append({"message": message, **context, **self.context})

    def validate(self) -> list[dict]:
        """Validates the schema element and returns a list of errors. This base method is extended in all child classes.

        Each error is represented as a dictionary containing the error message and any relevant context information.

        Returns:
            errors: A list of error dictionaries, with a 'message' key and any additional context (key-value pairs).
        """
        return self.errors
