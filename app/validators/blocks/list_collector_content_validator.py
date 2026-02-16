"""This module contains the ListCollectorContentValidator class, which validates the content of a list collector block.

Classes:
    ListCollectorContentValidator
"""

from app.error_messages import FOR_LIST_NEVER_POPULATED
from app.validators.blocks.block_validator import BlockValidator


class ListCollectorContentValidator(BlockValidator):
    """Validates the list collector of type ListCollectorContent.

    Methods:
        validate
        validate_for_list_is_valid
    """

    def validate(self):
        """Validates the list collector content block.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()
        self.validate_for_list_is_valid()
        return self.errors

    def validate_for_list_is_valid(self):
        """Validates that the 'for_list' property is valid. Verifies that the list for the list collector content block
        is either populated by a standard list collector or in the supplementary data lists property so populated
        by supplementary data.
        """
        list_name = self.block["for_list"]
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(
                FOR_LIST_NEVER_POPULATED,
                list_name=list_name,
            )
