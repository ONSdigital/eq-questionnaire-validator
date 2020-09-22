from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class BlockValidator(Validator):
    ANSWER_REFERENCE_INVALID = "Invalid answer reference"
    ANSWER_SELF_REFERENCE = "Invalid answer reference (self-reference)"
    LIST_REFERENCE_INVALID = "Invalid list reference"
    METADATA_REFERENCE_INVALID = "Invalid metadata reference"
    SELECTOR_USED_FOR_NON_ADDRESS_TYPE = "Invalid use of selector"

    ACTION_PARAMS_MISSING = "Action params key missing"
    ACTION_PARAMS_SHOULDNT_EXIST = "Action params key should not exist"

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
        self.validate_redirect_to_list_add_block_params()

        return self.errors

    def validate_source_references(self, source_references):
        for source_reference in source_references:
            source = source_reference["source"]
            if isinstance(source_reference["identifier"], str):
                identifiers = [source_reference["identifier"]]
            else:
                identifiers = source_reference["identifier"]

            if source == "answers":
                has_selector = "selector" in source_reference
                self.validate_answer_source_reference(identifiers, has_selector)

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

    def validate_answer_source_reference(self, identifiers, has_selector=False):
        answers_with_context = self.questionnaire_schema.answers_with_context

        for identifier in identifiers:
            if identifier not in answers_with_context:
                self.add_error(self.ANSWER_REFERENCE_INVALID, referenced_id=identifier)
            elif answers_with_context[identifier]["block"] == self.block["id"]:
                self.add_error(self.ANSWER_SELF_REFERENCE, referenced_id=identifier)

            if (
                has_selector
                and answers_with_context[identifier]["answer"]["type"] != "Address"
            ):
                self.add_error(
                    self.SELECTOR_USED_FOR_NON_ADDRESS_TYPE, referenced_id=identifier
                )

    def validate_redirect_to_list_add_block_params(self):
        questions = self.questionnaire_schema.get_all_questions_for_block(self.block)

        for question in questions:
            for answer in question["answers"]:
                for option in answer.get("options", []):
                    action = option.get("action")

                    if action and action["type"] == "RedirectToListAddBlock":
                        params = action.get("params")
                        is_list_collector = self.block["type"] in [
                            "ListCollector",
                            "PrimaryPersonListCollector",
                        ]

                        if is_list_collector and params:
                            self.add_error(
                                self.ACTION_PARAMS_SHOULDNT_EXIST, block_id=self.block
                            )

                        elif not is_list_collector and not params:
                            self.add_error(
                                self.ACTION_PARAMS_MISSING, block_id=self.block
                            )
