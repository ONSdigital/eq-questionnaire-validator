from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class BlockValidator(Validator):
    METADATA_REFERENCE_INVALID = "Invalid metadata reference"
    ANSWER_REFERENCE_INVALID = "Invalid answer reference"
    LIST_REFERENCE_INVALID = "Invalid list reference"
    ANSWER_SELF_REFERENCE = "Invalid answer reference (self-reference)"
    LIST_NAME_MISSING = "List name defined in action params does not exist"
    BLOCK_ID_MISSING = "Block id defined in action params does not exist"
    ACTION_PARAMS_MISSING = "Action params does not exist"

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

        if self.block["type"] not in ["ListCollector", "PrimaryPersonListCollector"]:
            self.validate_answer_actions_redirect_to_list_add_block_params()

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

    def validate_answer_actions_redirect_to_list_add_block_params(self):
        collector_questions = self.questionnaire_schema.get_all_questions_for_block(
            self.block
        )

        for collector_question in collector_questions:
            for collector_answer in collector_question["answers"]:
                for option in collector_answer.get("options", []):
                    action = option.get("action")

                    if action:
                        params = action.get("params")
                        if not params:
                            self.add_error(
                                self.ACTION_PARAMS_MISSING, block_id=self.block
                            )
                            continue

                        list_name = params.get("list_name")

                        if (
                            list_name
                            and list_name not in self.questionnaire_schema.list_names
                        ):
                            self.add_error(self.LIST_NAME_MISSING, list_name=list_name)

                        block_id = params.get("block_id")

                        if (
                            block_id
                            and block_id not in self.questionnaire_schema.block_ids
                        ):
                            self.add_error(self.BLOCK_ID_MISSING, block_id=block_id)
