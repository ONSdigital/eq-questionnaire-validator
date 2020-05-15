from app import error_messages
from app.validators.placeholders.block_placeholder_validator import (
    BlockPlaceholderValidator,
)
from app.validators.validator import Validator


class BlockValidator(Validator):
    def __init__(self, block_element, questionnaire_schema):
        super().__init__(block_element)
        self.questionnaire_schema = questionnaire_schema
        self.block = block_element
        self.context["block_id"] = self.block["id"]

    def validate(self):
        """
        Validation called for every block type
        """
        source_references = self.questionnaire_schema.get_block_key_context(
            self.block["id"], "identifier"
        )

        self.validate_source_references(source_references, self.block["id"])
        placeholder_validator = BlockPlaceholderValidator(
            self.block, self.questionnaire_schema
        )
        placeholder_validator.validate()

        self.errors += placeholder_validator.errors

    def validate_source_references(self, source_references, block_id):
        for source_reference in source_references:
            source = source_reference["source"]
            if isinstance(source_reference["identifier"], str):
                identifiers = [source_reference["identifier"]]
            else:
                identifiers = source_reference["identifier"]

            if source == "answers":
                self.validate_answer_source_reference(identifiers, block_id)

            elif source == "metadata":
                self._validate_metadata_source_reference(identifiers, block_id)

            elif source == "list":
                self.validate_list_source_reference(identifiers, block_id)

    def _validate_metadata_source_reference(self, identifiers, current_block_id):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.metadata_ids:
                self.add_error(
                    error_messages.METADATA_REFERENCE_INVALID,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )

    def validate_list_source_reference(self, identifiers, current_block_id):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.list_names:
                self.add_error(
                    error_messages.LIST_REFERENCE_INVALID,
                    id=identifier,
                    block_id=current_block_id,
                )

    def validate_answer_source_reference(self, identifiers, current_block_id):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.answers_with_context:
                self.add_error(
                    error_messages.ANSWER_REFERENCE_INVALID,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )
            elif (
                self.questionnaire_schema.answers_with_context[identifier]["block"]
                == current_block_id
            ):
                self.add_error(
                    error_messages.ANSWER_SELF_REFERENCE,
                    referenced_id=identifier,
                    block_id=current_block_id,
                )
