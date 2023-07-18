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
    LIST_COLLECTOR_KEY_MISSING = "Missing key in ListCollectorContent"
    NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR = (
        "List may only have one List Collector and List Collector Content, if "
        "the List Collector Content features Repeating Blocks"
    )

    def validate(self):
        super().validate()

        validate_repeating_blocks_list_collectors(
            self, "ListCollectorContent", "ListCollector"
        )

        return self.errors
