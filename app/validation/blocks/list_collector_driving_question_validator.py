from app.validation import error_messages
from app.validation.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    def __init__(self, block, section_id, questionnaire_schema):
        self.block = block
        self.section_id = section_id
        super(ListCollectorDrivingQuestionValidator, self).__init__(block)
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        if not self.questionnaire_schema.has_single_list_collector(
            self.block["for_list"], self.section_id
        ):
            block = self.block
            self.add_error(
                f'ListCollectorDrivingQuestion `{block["id"]}` for list '
                f'`{block["for_list"]}` cannot be used with multiple ListCollectors'
            )

        if not self.questionnaire_schema.has_single_driving_question(
            self.block["for_list"]
        ):
            self.add_error(
                error_messages.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
                block_id=self.block["id"],
                for_list=self.block["for_list"],
            )
