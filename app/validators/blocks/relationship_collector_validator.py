"""This module contains the RelationshipCollectorValidator class, which is responsible for validating blocks of type
"RelationshipCollector" in a questionnaire schema.

Classes:
    RelationshipCollectorValidator
"""

from app import error_messages
from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.unrelated_block_validator import UnrelatedBlockValidator


class RelationshipCollectorValidator(BlockValidator):
    """Validate blocks of type "RelationshipCollector" in a questionnaire schema.

    Methods:
        validate
        validate_answer_type
        validate_multiple_answers
        validate_list_exists
        validate_unrelated_block
    """

    RELATIONSHIP_COLLECTOR_HAS_INVALID_ANSWER_TYPE = (
        "Only answers of type Relationship are valid in RelationshipCollector blocks."
    )
    RELATIONSHIP_COLLECTOR_HAS_MULTIPLE_ANSWERS = "RelationshipCollector contains more than one answer."

    def validate(self):
        """Validate the RelationshipCollector block by invoking specific validation methods in order.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()

        self.validate_list_exists()
        self.validate_multiple_answers()
        self.validate_answer_type()
        self.validate_unrelated_block()

        return self.errors

    def validate_answer_type(self):
        """Validate that the answer type of the first answer in the block is of type 'Relationship'."""
        if self.questionnaire_schema.get_first_answer_in_block(self.block["id"])["type"] != "Relationship":
            self.add_error(self.RELATIONSHIP_COLLECTOR_HAS_INVALID_ANSWER_TYPE)

    def validate_multiple_answers(self):
        """Validate that there is only one answer in the block."""
        answer_ids = self.questionnaire_schema.get_all_answer_ids(self.block["id"])

        if len(answer_ids) > 1:
            self.add_error(self.RELATIONSHIP_COLLECTOR_HAS_MULTIPLE_ANSWERS)

    def validate_list_exists(self):
        """Validate that the list specified in the 'for_list' property of the block is used in the questionnaire
        schema.
        """
        list_name = self.block["for_list"]

        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

    def validate_unrelated_block(self):
        """Validate the unrelated block if it exists.It creates instance of UnrelatedBlockValidator to validate
        the unrelated block.
        """
        if "unrelated_block" in self.block:
            block_validator = UnrelatedBlockValidator(
                self.block["unrelated_block"],
                self.questionnaire_schema,
            )
            self.errors += block_validator.validate()
