from app import error_messages
from app.validators.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    def validate(self):
        super(ListCollectorDrivingQuestionValidator, self).validate()

        if not self.questionnaire_schema.has_single_driving_question(
            self.block["for_list"]
        ):
            self.add_error(
                error_messages.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
                block_id=self.block["id"],
                for_list=self.block["for_list"],
            )
