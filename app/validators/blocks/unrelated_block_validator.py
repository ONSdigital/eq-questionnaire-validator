""""UnrelatedBlockValidator class to validate unrelated blocks in a questionnaire schema."""

from app.validators.blocks.block_validator import BlockValidator


class UnrelatedBlockValidator(BlockValidator):
    """UnrelatedBlockValidator validates unrelated blocks in a questionnaire schema."""
    ACTION_PARAMS_MISSING = "RemoveUnrelatedRelationships and AddUnrelatedRelationships actions must be present"

    def validate(self):
        """Validate the unrelated block."""
        super().validate()
        self.validate_answer_actions()
        return self.errors

    def validate_answer_actions(self):
        """Validate that the actions for unrelated blocks are present."""
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
