from app.validators.blocks.block_validator import BlockValidator
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
        try:
            self.validate_repeating_blocks_list_collector_content()
        except KeyError as e:
            self.add_error(self.LIST_COLLECTOR_KEY_MISSING, key=e)

        return self.errors

    def validate_repeating_blocks_list_collector_content(self):
        if self.block.get("repeating_blocks"):
            list_name = self.block["for_list"]

            other_list_collectors = self.questionnaire_schema.get_other_blocks(
                self.block["id"], for_list=list_name, type="ListCollector"
            )
            other_list_collector_contents = self.questionnaire_schema.get_other_blocks(
                self.block["id"], for_list=list_name, type="ListCollectorContent"
            )

            if (
                other_list_collectors and len(other_list_collectors) > 1
            ) or other_list_collector_contents:
                self.add_error(
                    self.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
                    list_name=list_name,
                )
