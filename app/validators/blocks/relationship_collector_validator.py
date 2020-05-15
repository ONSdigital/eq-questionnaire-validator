from app import error_messages
from app.validators.blocks.block_validator import BlockValidator


class RelationshipCollectorValidator(BlockValidator):
    def validate(self):
        super(RelationshipCollectorValidator, self).validate()

        self.validate_list_exists()

        answer_ids = self.questionnaire_schema.get_all_answer_ids(self.block["id"])

        if len(answer_ids) > 1:
            self.add_error(error_messages.RELATIONSHIP_COLLECTOR_HAS_MULTIPLE_ANSWERS)
        if (
            self.questionnaire_schema.get_first_answer_in_block(self.block["id"])[
                "type"
            ]
            != "Relationship"
        ):
            self.add_error(
                error_messages.RELATIONSHIP_COLLECTOR_HAS_INVALID_ANSWER_TYPE
            )

    def validate_list_exists(self):
        list_name = self.block["for_list"]

        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)
