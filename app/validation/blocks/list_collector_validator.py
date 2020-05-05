from app.validation import error_messages
from app.validation.blocks.block_validator import BlockValidator


class ListCollectorValidator(BlockValidator):
    def __init__(self, block, questionnaire_schema):
        super(ListCollectorValidator, self).__init__(block)
        self.questionnaire_schema = questionnaire_schema

    def validate(self):
        self._validate_list_answer_references(self.block)

        self.validate_collector_questions(
            self.block,
            self.block["add_answer"]["value"],
            error_messages.NO_RADIO_FOR_LIST_COLLECTOR,
            error_messages.NON_EXISTENT_LIST_COLLECTOR_ADD_ANSWER_VALUE,
        )

        self.validate_collector_questions(
            self.block["remove_answer"],
            self.block["remove_answer"]["value"],
            error_messages.NO_RADIO_FOR_LIST_COLLECTOR_REMOVE,
            error_messages.NON_EXISTENT_LIST_COLLECTOR_REMOVE_ANSWER_VALUE,
        )

        self.validate_list_collector_answer_ids(self.block)
        self.validate_other_list_collectors()

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

    def validate_collector_questions(
        self, block, answer_value, missing_radio_error, missing_value_error
    ):
        collector_questions = self.questionnaire_schema.get_all_questions_for_block(
            block
        )

        for collector_question in collector_questions:
            for collector_answer in collector_question["answers"]:
                if collector_answer["type"] != "Radio":
                    self.add_error(missing_radio_error)

                if not _options_contain_value(
                    collector_answer["options"], answer_value
                ):
                    self.add_error(missing_value_error)

    def validate_list_collector_answer_ids(self, block):
        """
        - Ensure that answer_ids on add blocks match between all blocks that populate a single list.
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

        other_list_collectors = self.questionnaire_schema.get_other_list_collectors(
            list_name, block_id_to_filter=self.block["id"]
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


def _options_contain_value(options, value):
    for option in options:
        if option["value"] == value:
            return True
