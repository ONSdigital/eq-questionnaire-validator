"""This module contains the ListCollectorDrivingQuestionValidator class.

Classes:
    ListCollectorDrivingQuestionValidator
"""

from app.validators.blocks.block_validator import BlockValidator


class ListCollectorDrivingQuestionValidator(BlockValidator):
    """Validate the list collector driving question block.

    Methods:
        validate
    """

    MULTIPLE_DRIVING_QUESTIONS_FOR_LIST = "The block_id should be the only ListCollectorDrivingQuestion for list"

    def validate(self):
        """Validate using the existing QuestionnaireSchema method has_single_driving_question to check that the
        block is the only ListCollectorDrivingQuestion for the list.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
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
