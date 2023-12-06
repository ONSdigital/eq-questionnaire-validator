from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class ListCollectorValidator(BlockValidator, ValidateListCollectorQuestionsMixin):
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
    NON_UNIQUE_ANSWER_ID_FOR_SAME_LIST_COLLECTOR_ADD_BLOCK = "Multiple list collectors with same name populate a list using different answer_ids in add block"
    DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR_ADD_BLOCK = "Different list collectors populate a list using duplicate answer_ids in the add block"
    NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR = "List may only have one List Collector, if the List Collector features Repeating Blocks"

    def validate(self):
        super().validate()
        try:
            collector_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block
            )
            self.validate_collector_questions(
                collector_questions,
                self.NO_RADIO_FOR_LIST_COLLECTOR,
                self.REDIRECT_TO_LIST_ADD_BLOCK_ACTION,
                self.NO_REDIRECT_TO_LIST_ADD_BLOCK_ACTION,
            )
            answer_ids = self.questionnaire_schema.get_list_collector_answer_ids(
                self.block["id"]
            )
            self.validate_same_name_answer_ids(answer_ids)
            collector_remove_questions = (
                self.questionnaire_schema.get_all_questions_for_block(
                    self.block["remove_block"]
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
        """
        - Ensure that answer_ids on add and edit blocks match between all blocks that populate a single list.
        - Enforce the same answer_ids on add and edit sub-blocks
        """
        add_answer_ids = self.questionnaire_schema.get_all_answer_ids(
            block["add_block"]["id"]
        )
        edit_answer_ids = self.questionnaire_schema.get_all_answer_ids(
            block["edit_block"]["id"]
        )

        if add_answer_ids.symmetric_difference(edit_answer_ids):
            self.add_error(
                self.LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH, block_id=block["id"]
            )

    def validate_not_for_supplementary_list(self):
        """
        Standard list collectors cannot be used for a supplementary list, as these may not be edited
        """
        if self.block["for_list"] in self.questionnaire_schema.supplementary_lists:
            self.add_error(
                self.LIST_COLLECTOR_FOR_SUPPLEMENTARY_LIST_IS_INVALID,
                list_name=self.block["for_list"],
            )

    def validate_other_list_collectors(self):
        list_name = self.block["for_list"]
        add_answer_ids = self.questionnaire_schema.get_all_answer_ids(
            self.block["add_block"]["id"]
        )

        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"], type="ListCollector"
        )

        for other_list_collector in other_list_collectors:
            other_list_collector_name = other_list_collector["for_list"]
            other_add_ids = self.questionnaire_schema.get_all_answer_ids(
                other_list_collector["add_block"]["id"]
            )

            are_list_collector_names_matching = (
                other_list_collector_name == list_name
            )
            contains_duplicate_add_answer_ids = any(
                add_answer_id in other_add_ids for add_answer_id in add_answer_ids
            )

            # Check for duplicate answer IDs for the same list collector
            if are_list_collector_names_matching and add_answer_ids.symmetric_difference(other_add_ids):
                self.add_error(
                    self.NON_UNIQUE_ANSWER_ID_FOR_SAME_LIST_COLLECTOR_ADD_BLOCK,
                    list_name=list_name,
                )

            # Check for duplicate answer IDs for a different list collector
            if not are_list_collector_names_matching and contains_duplicate_add_answer_ids:
                self.add_error(
                    self.DUPLICATE_ANSWER_ID_FOR_DIFFERENT_LIST_COLLECTOR_ADD_BLOCK,
                    list_name=list_name,
                    other_list_collector_name=other_list_collector_name,
                    other_list_collector_block_id=other_list_collector["id"],
                )

    def validate_single_repeating_blocks_list_collector(self):
        if not self.block.get("repeating_blocks"):
            return
        list_name = self.block["for_list"]
        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"], for_list=list_name, type="ListCollector"
        )
        if other_list_collectors:
            self.add_error(
                ListCollectorValidator.NON_SINGLE_REPEATING_BLOCKS_LIST_COLLECTOR,
                list_name=list_name,
            )
