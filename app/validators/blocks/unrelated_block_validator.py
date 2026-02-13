"""Validator for blocks that contain unrelated relationship actions.

Classes:
    UnrelatedBlockValidator
"""

from app.validators.blocks.block_validator import BlockValidator


class UnrelatedBlockValidator(BlockValidator):
    """Validates blocks that contain unrelated relationship actions.

    Methods:
        validate
        validate_answer_actions
    """
    ACTION_PARAMS_MISSING = "RemoveUnrelatedRelationships and AddUnrelatedRelationships actions must be present"

    def validate(self):
        """Validates the block by invoking the base validation and then validate_answer_actions.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
        super().validate()
        self.validate_answer_actions()
        return self.errors

    def validate_answer_actions(self):
        """Ensures that both AddUnrelatedRelationships and RemoveUnrelatedRelationships actions are present in the
        block's questions.
        """
        expected_actions = ["AddUnrelatedRelationships", "RemoveUnrelatedRelationships"]
        questions = self.questionnaire_schema.get_all_questions_for_block(self.block)
        for question in questions:
            actions = [
                option["action"]["type"]
                for answer in question["answers"]
                for option in answer["options"]
                if "action" in option
            ]

            if sorted(actions) != expected_actions:
                self.add_error(self.ACTION_PARAMS_MISSING)
