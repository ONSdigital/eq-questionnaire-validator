from app.validators.blocks.list_collector_validator import ListCollectorValidator
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class ListCollectorContentValidator(
    ListCollectorValidator, ValidateListCollectorQuestionsMixin
):
    def validate(self):
        self.validate_id_relationships_used_with_relationship_collector()
        self.validate_redirect_to_list_add_block_params()
        self.validate_placeholder_answer_self_references()

        self.validate_repeating_blocks_list_collectors(
            "ListCollectorContent", "ListCollector"
        )

        return self.errors
