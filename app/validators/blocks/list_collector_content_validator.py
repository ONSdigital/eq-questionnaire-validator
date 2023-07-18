from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.list_collector_validator import (
    validate_repeating_blocks_list_collectors,
)
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class ListCollectorContentValidator(
    BlockValidator, ValidateListCollectorQuestionsMixin
):
    def validate(self):
        super().validate()

        validate_repeating_blocks_list_collectors(
            self, "ListCollectorContent", "ListCollector"
        )

        return self.errors
