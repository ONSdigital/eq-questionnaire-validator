from app import error_messages
from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.validate_collector_quesitons_mixin import (
    ValidateCollectorQuestionsMixin,
)


class ListCollectorValidator(BlockValidator, ValidateCollectorQuestionsMixin):
    def validate(self):
        super().validate()

        try:
            self._validate_list_answer_references(self.block)

            collector_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block
            )

            self.validate_collector_questions(
                collector_questions,
                self.block["add_answer"]["value"],
                error_messages.NO_RADIO_FOR_LIST_COLLECTOR,
                error_messages.NON_EXISTENT_LIST_COLLECTOR_ADD_ANSWER_VALUE,
            )

            collector_remove_questions = self.questionnaire_schema.get_all_questions_for_block(
                self.block["remove_answer"]
            )

            self.validate_collector_questions(
                collector_remove_questions,
                self.block["remove_answer"]["value"],
                error_messages.NO_RADIO_FOR_LIST_COLLECTOR_REMOVE,
                error_messages.NON_EXISTENT_LIST_COLLECTOR_REMOVE_ANSWER_VALUE,
            )

            self.validate_list_collector_answer_ids(self.block)
            self.validate_other_list_collectors()
        except KeyError as e:
            self.add_error(error_messages.LIST_COLLECTOR_KEY_MISSING, key=e)

    def _validate_list_answer_references(self, block):
        main_block_ids = self.questionnaire_schema.get_all_answer_ids(block["id"])
        remove_block_ids = self.questionnaire_schema.get_all_answer_ids(
            block["remove_block"]["id"]
        )

        if block["add_answer"]["id"] not in main_block_ids:
            self.add_error(
                error_messages.ADD_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK,
                referenced_id=block["add_answer"]["id"],
            )
        if block["remove_answer"]["id"] not in remove_block_ids:
            self.add_error(
                error_messages.REMOVE_ANSWER_REFERENCE_NOT_IN_REMOVE_BLOCK,
                referenced_id=block["remove_answer"]["id"],
            )

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
                error_messages.LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH,
                block_id=block["id"],
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
                    error_messages.NON_UNIQUE_ANSWER_ID_FOR_LIST_COLLECTOR_ADD,
                    list_name=list_name,
                )
