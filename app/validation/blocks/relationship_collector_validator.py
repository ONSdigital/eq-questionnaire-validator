from app.validation import error_messages
from app.validation.blocks.block_validator import BlockValidator


class RelationshipCollectorValidator(BlockValidator):
    def __init__(self, block, questionnaire_schema):
        self.block = block
        self.questionnaire_schema = questionnaire_schema
        super(RelationshipCollectorValidator, self).__init__(block)

    def validate(self):
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
