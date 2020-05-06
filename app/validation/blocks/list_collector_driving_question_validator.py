from app.validation import error_messages
from app.validation.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    def validate(self):
        if not self.questionnaire_schema.has_single_list_collector(
            self.block["for_list"]
        ):
            self.add_error(
                error_messages.MULTIPLE_LIST_COLLECTORS_FOR_DRIVING_QUESTION,
                list_name=self.block["for_list"],
            )

        if not self.questionnaire_schema.has_single_driving_question(
            self.block["for_list"]
        ):
            self.add_error(
                error_messages.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
                block_id=self.block["id"],
                for_list=self.block["for_list"],
            )
