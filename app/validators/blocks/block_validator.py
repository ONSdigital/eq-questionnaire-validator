from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.validator import Validator


class BlockValidator(Validator):
    ACTION_PARAMS_MISSING = "Action params key missing"
    ACTION_PARAMS_SHOULDNT_EXIST = "Action params key should not exist"
    ID_RELATIONSHIPS_NOT_USED_WITH_RELATIONSHIP_COLLECTOR = "Invalid use of id relationships, can only be used with RelationshipCollector block type"
    PLACEHOLDER_ANSWER_SELF_REFERENCE = (
        "Placeholder references an answer in the same block (self-reference)"
    )

    def __init__(self, block_element, questionnaire_schema):
        super().__init__(block_element)
        self.questionnaire_schema = questionnaire_schema
        self.block = block_element
        self.context["block_id"] = self.block["id"]

    def validate(self):
        """
        Validation called for every block type
        """
        self.validate_id_relationships_used_with_relationship_collector()
        self.validate_redirect_to_list_add_block_params()
        self.validate_placeholder_answer_self_references()

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

    def validate_placeholder_answer_self_references(self):
        source_references = get_object_containing_key(self.block, "identifier")
        for json_path, source_reference in source_references:
            if source_reference["source"] == "answers":
                identifiers = (
                    source_reference["identifier"]
                    if isinstance(source_reference["identifier"], list)
                    else [source_reference["identifier"]]
                )
                for identifier in identifiers:
                    if (
                        "placeholders" in json_path
                        and identifier in self.questionnaire_schema.answers_with_context
                        and self.questionnaire_schema.answers_with_context[identifier][
                            "block"
                        ]
                        == self.block["id"]
                    ):
                        self.add_error(
                            self.PLACEHOLDER_ANSWER_SELF_REFERENCE,
                            identifier=identifier,
                        )
