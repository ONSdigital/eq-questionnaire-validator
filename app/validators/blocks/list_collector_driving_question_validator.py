from app.validators.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    MULTIPLE_DRIVING_QUESTIONS_FOR_LIST = (
        "The block_id should be the only ListCollectorDrivingQuestion for list"
    )

    def validate(self):
        super().validate()

        if not self.questionnaire_schema.has_single_driving_question(
            self.block["for_list"]
        ):
            self.add_error(
                self.MULTIPLE_DRIVING_QUESTIONS_FOR_LIST,
                block_id=self.block["id"],
                for_list=self.block["for_list"],
            )
        return self.errors
