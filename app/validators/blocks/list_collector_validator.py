"""ListCollectorValidator class to validate list collector blocks in a questionnaire schema."""

from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class ListCollectorValidator(BlockValidator, ValidateListCollectorQuestionsMixin):
    """ListCollectorValidator validates list collector blocks in a questionnaire schema."""

    LIST_COLLECTOR_KEY_MISSING = "Missing key in ListCollector"
    REDIRECT_TO_LIST_ADD_BLOCK_ACTION = "RedirectToListAddBlock"
    REMOVE_LIST_ITEM_AND_ANSWERS_ACTION = "RemoveListItemAndAnswers"

    NO_REDIRECT_TO_LIST_ADD_BLOCK_ACTION = (
        f"{REDIRECT_TO_LIST_ADD_BLOCK_ACTION} action not found"
    )
    NO_REMOVE_LIST_ITEM_AND_ANSWERS_ACTION = (
        f"{REDIRECT_TO_LIST_ADD_BLOCK_ACTION} action not found"
    )
    NO_RADIO_FOR_LIST_COLLECTOR = (
        "The list collector block does not contain a Radio answer type"
    )
    NO_RADIO_FOR_LIST_COLLECTOR_REMOVE = (
        "The list collector remove block does not contain a Radio answer type"
    )
    LIST_COLLECTOR_FOR_SUPPLEMENTARY_LIST_IS_INVALID = "Non content list collectors cannot be for a list which comes from supplementary data"
    LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH = "The list collector block contains an add block and edit block with different answer ids"
    DIFFERENT_LIST_COLLECTOR_ADD_BLOCKS_FOR_SAME_LIST = "Multiple list collectors with same name populate a list using different answer_ids in add block"
    DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR = "Different list collectors populate a list using duplicate answer_ids in a list block"
    LIST_COLLECTOR_ANSWER_ID_USED_ELSEWHERE = "List collector child block answer_id is already used elsewhere outside the list collector"
    NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR = "List may only have one List Collector, if the List Collector features Repeating Blocks"

    def validate(self):
        """Validate the list collector block."""
        super().validate()
        try:
            collector_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block,
            )
            self.validate_collector_questions(
                collector_questions,
                self.NO_RADIO_FOR_LIST_COLLECTOR,
                self.REDIRECT_TO_LIST_ADD_BLOCK_ACTION,
                self.NO_REDIRECT_TO_LIST_ADD_BLOCK_ACTION,
            )
            answer_ids = self.questionnaire_schema.get_list_collector_answer_ids(
                self.block["id"],
            )
            self.validate_same_name_answer_ids(answer_ids)
            collector_remove_questions = (
                self.questionnaire_schema.get_all_questions_for_block(
                    self.block["remove_block"],
                )
            )
            self.validate_collector_questions(
                collector_remove_questions,
                self.NO_RADIO_FOR_LIST_COLLECTOR_REMOVE,
                self.REMOVE_LIST_ITEM_AND_ANSWERS_ACTION,
                self.NO_REMOVE_LIST_ITEM_AND_ANSWERS_ACTION,
            )
            self.validate_list_collector_answer_ids(self.block)
            self.validate_other_list_collectors()
            self.validate_single_repeating_blocks_list_collector()
            self.validate_not_for_supplementary_list()
        except KeyError as e:
            self.add_error(self.LIST_COLLECTOR_KEY_MISSING, key=e)

        return self.errors

    def validate_list_collector_answer_ids(self, block):
        """Validate the answer_ids for the list collector block.

        - Ensure that answer_ids on add and edit blocks match between all blocks that populate a single list.
        - Enforce the same answer_ids on add and edit sub-blocks
        - Ensure that that child block answer_ids are not used elsewhere in the schema that's not another list collector
        """
        list_answer_ids = (
            self.questionnaire_schema.get_list_collector_answer_ids_by_child_block(
                block["id"],
            )
        )

        if list_answer_ids["add_block"].symmetric_difference(
            list_answer_ids["edit_block"],
        ):
            self.add_error(
                self.LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH,
                block_id=block["id"],
            )

        all_schema_ids_excluding_list_collectors = self.questionnaire_schema.ids
        for child_block in list_answer_ids:
            if list_answer_ids[child_block].intersection(
                all_schema_ids_excluding_list_collectors,
            ):
                self.add_error(
                    self.LIST_COLLECTOR_ANSWER_ID_USED_ELSEWHERE,
                    block_id=block["id"],
                    list_child_block_name=child_block,
                )

    def validate_not_for_supplementary_list(self):
        """Validate that the list collector is not for a supplementary list.

        Standard list collectors cannot be used for a supplementary list, as these may not be edited.
        If the list collector is for a supplementary list, an error is added.
        """
        if self.block["for_list"] in self.questionnaire_schema.supplementary_lists:
            self.add_error(
                self.LIST_COLLECTOR_FOR_SUPPLEMENTARY_LIST_IS_INVALID,
                list_name=self.block["for_list"],
            )

    def validate_other_list_collectors(self):
        """Validate other list collectors in the schema.

        Checks other list collectors for:
        - non-unique answer id in add block for any other same-named list collectors
        - duplicate answer id in add, edit, or remove block for other different-named list collectors
        """
        list_answer_ids = (
            self.questionnaire_schema.get_list_collector_answer_ids_by_child_block(
                self.block["id"],
            )
        )
        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"],
            type="ListCollector",
        )

        for other_list_collector in other_list_collectors:
            other_list_answer_ids = (
                self.questionnaire_schema.get_list_collector_answer_ids_by_child_block(
                    other_list_collector["id"],
                )
            )

            if self.block["for_list"] == other_list_collector["for_list"]:
                if list_answer_ids["add_block"].symmetric_difference(
                    other_list_answer_ids["add_block"],
                ):
                    self.add_error(
                        self.DIFFERENT_LIST_COLLECTOR_ADD_BLOCKS_FOR_SAME_LIST,
                        list_name=self.block["for_list"],
                        other_list_block_id=other_list_collector["id"],
                    )
            else:
                for child_block in other_list_answer_ids:
                    if other_list_answer_ids[child_block].intersection(
                        list_answer_ids[child_block],
                    ):
                        self.add_error(
                            self.DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR,
                            list_name=self.block["for_list"],
                            list_child_block_name=child_block,
                            other_list_name=other_list_collector["for_list"],
                            other_list_block_id=other_list_collector["id"],
                        )

    def validate_single_repeating_blocks_list_collector(self):
        """Validate that only one repeating block is present for the list collector."""
        if not self.block.get("repeating_blocks"):
            return
        list_name = self.block["for_list"]
        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"],
            for_list=list_name,
            type="ListCollector",
        )
        if other_list_collectors:
            self.add_error(
                ListCollectorValidator.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
                list_name=list_name,
            )
