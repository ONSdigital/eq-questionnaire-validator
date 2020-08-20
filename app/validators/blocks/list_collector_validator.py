from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class ListCollectorValidator(BlockValidator, ValidateListCollectorQuestionsMixin):
    LIST_COLLECTOR_KEY_MISSING = "Missing key in ListCollector"
    REDIRECT_TO_ADD_BLOCK = "RedirectToAddBlock"
    REDIRECT_TO_REMOVE_BLOCK = "RemoveAnswersForListItem"

    NO_RADIO_FOR_LIST_COLLECTOR = (
        "The list collector block does not contain a Radio answer type"
    )

    NO_RADIO_FOR_LIST_COLLECTOR_REMOVE = (
        "The list collector remove block does not contain a Radio answer type"
    )

    NO_REDIRECT_TO_ADD_BLOCK = "RedirectToAddBlock action not found"

    NO_REDIRECT_TO_REMOVE_BLOCK = "RemoveAnswersForListItem action not found"

    LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH = (
        "The list collector block contains an add block and edit block"
        " with different answer ids"
    )

    NON_UNIQUE_ANSWER_ID_FOR_LIST_COLLECTOR_ADD = (
        "Multiple list collectors populate a list using different "
        "answer_ids in the add block"
    )

    def validate(self):
        super().validate()
        try:
            collector_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block
            )
            self.validate_collector_questions(
                collector_questions,
                self.NO_RADIO_FOR_LIST_COLLECTOR,
                self.REDIRECT_TO_ADD_BLOCK,
                self.NO_REDIRECT_TO_ADD_BLOCK,
            )

            collector_remove_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block["remove_block"]
            )
            self.validate_collector_questions(
                collector_remove_questions,
                self.NO_RADIO_FOR_LIST_COLLECTOR_REMOVE,
                self.REDIRECT_TO_REMOVE_BLOCK,
                self.NO_REDIRECT_TO_REMOVE_BLOCK,
            )
            self.validate_list_collector_answer_ids(self.block)
            self.validate_other_list_collectors()
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

    def validate_other_list_collectors(self):
        list_name = self.block["for_list"]
        add_answer_ids = self.questionnaire_schema.get_all_answer_ids(
            self.block["add_block"]["id"]
        )

        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"], for_list=list_name, type="ListCollector"
        )

        for other_list_collector in other_list_collectors:
            other_add_ids = self.questionnaire_schema.get_all_answer_ids(
                other_list_collector["add_block"]["id"]
            )
            difference = add_answer_ids.symmetric_difference(other_add_ids)
            if difference:
                self.add_error(
                    self.NON_UNIQUE_ANSWER_ID_FOR_LIST_COLLECTOR_ADD,
                    list_name=list_name,
                )
