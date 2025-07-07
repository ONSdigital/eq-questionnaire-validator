"""ListCollectorDrivingQuestionValidator validates driving questions for list collector blocks in a questionnaire schema."""

from app.validators.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    """ListCollectorDrivingQuestionValidator validates driving questions for list collector blocks in a questionnaire schema."""

    MULTIPLE_DRIVING_QUESTIONS_FOR_LIST = (
        "The block_id should be the only ListCollectorDrivingQuestion for list"
    )

    def validate(self):
        """Validates that there is only one driving question for the specified list."""
        super().validate()

        if not self.questionnaire_schema.has_single_driving_question(
            self.block["for_list"],
        ):
            self.add_error(
                self.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
                block_id=self.block["id"],
                for_list=self.block["for_list"],
            )
        return self.errors
