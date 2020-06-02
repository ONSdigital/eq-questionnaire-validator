from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class BlockValidator(Validator):
    METADATA_REFERENCE_INVALID = "Invalid metadata reference"
    ANSWER_REFERENCE_INVALID = "Invalid answer reference"
    LIST_REFERENCE_INVALID = "Invalid list reference"
    ANSWER_SELF_REFERENCE = "Invalid answer reference (self-reference)"

    def __init__(self, block_element, questionnaire_schema):
        super().__init__(block_element)
        self.questionnaire_schema = questionnaire_schema
        self.block = block_element
        self.context["block_id"] = self.block["id"]

    def validate(self):
        """
        Validation called for every block type
        """
        source_references = get_object_containing_key(self.block, "identifier")

        self.validate_source_references(source_references)

        return self.errors

    def validate_source_references(self, source_references):
        for source_reference in source_references:
            source = source_reference["source"]
            if isinstance(source_reference["identifier"], str):
                identifiers = [source_reference["identifier"]]
            else:
                identifiers = source_reference["identifier"]

            if source == "answers":
                self.validate_answer_source_reference(identifiers)

            elif source == "metadata":
                self.validate_metadata_source_reference(identifiers)

            elif source == "list":
                self.validate_list_source_reference(identifiers)

    def validate_metadata_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.metadata_ids:
                self.add_error(
                    self.METADATA_REFERENCE_INVALID, referenced_id=identifier
                )

    def validate_list_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.list_names:
                self.add_error(self.LIST_REFERENCE_INVALID, id=identifier)

    def validate_answer_source_reference(self, identifiers):
        for identifier in identifiers:
            if identifier not in self.questionnaire_schema.answers_with_context:
                self.add_error(self.ANSWER_REFERENCE_INVALID, referenced_id=identifier)
            elif (
                self.questionnaire_schema.answers_with_context[identifier]["block"]
                == self.block["id"]
            ):
                self.add_error(self.ANSWER_SELF_REFERENCE, referenced_id=identifier)
