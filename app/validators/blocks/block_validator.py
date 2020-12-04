from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class BlockValidator(Validator):
    ACTION_PARAMS_MISSING = "Action params key missing"
    ACTION_PARAMS_SHOULDNT_EXIST = "Action params key should not exist"
    ANSWER_REFERENCE_INVALID = "Invalid answer reference"
    ANSWER_SELF_REFERENCE = "Invalid answer reference (self-reference)"
    COMPOSITE_ANSWER_INVALID = "Invalid composite answer"
    COMPOSITE_ANSWER_FIELD_INVALID = "Invalid field for composite answer"
    ID_RELATIONSHIPS_NOT_USED_WITH_RELATIONSHIP_COLLECTOR = "Invalid use of id relationships, can only be used with type RelationshipCollector"
    LIST_REFERENCE_INVALID = "Invalid list reference"
    METADATA_REFERENCE_INVALID = "Invalid metadata reference"

    COMPOSITE_ANSWERS_TO_SELECTORS_MAP = {
        "Address": ["line1", "line2", "town", "postcode"]
    }

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

        self.validate_id_relationships_used_with_relationship_collector()
        self.validate_source_references(source_references)
        self.validate_redirect_to_list_add_block_params()

        return self.errors

    def validate_id_relationships_used_with_relationship_collector(self):
        if (
            self.block["id"] == "relationships"
            and self.block["type"] != "RelationshipCollector"
        ):
            self.add_error(
                self.ID_RELATIONSHIPS_NOT_USED_WITH_RELATIONSHIP_COLLECTOR,
                block_id=self.block["id"],
            )

    def validate_source_references(self, source_references):
        for source_reference in source_references:
            source = source_reference["source"]
            if isinstance(source_reference["identifier"], str):
                identifiers = [source_reference["identifier"]]
            else:
                identifiers = source_reference["identifier"]

            if source == "answers":
                selector = source_reference.get("selector")
                self.validate_answer_source_reference(identifiers, selector)

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

    def validate_answer_source_reference(self, identifiers, selector=None):
        answers_with_context = self.questionnaire_schema.answers_with_context

        for identifier in identifiers:
            if identifier not in answers_with_context:
                self.add_error(self.ANSWER_REFERENCE_INVALID, referenced_id=identifier)

            elif answers_with_context[identifier]["block"] == self.block["id"]:
                self.add_error(self.ANSWER_SELF_REFERENCE, referenced_id=identifier)

            if selector:
                answer_type = answers_with_context[identifier]["answer"]["type"]

                if answer_type not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP:
                    self.add_error(
                        self.COMPOSITE_ANSWER_INVALID, referenced_id=identifier
                    )
                elif (
                    selector not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP[answer_type]
                ):
                    self.add_error(
                        self.COMPOSITE_ANSWER_FIELD_INVALID, referenced_id=identifier
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
