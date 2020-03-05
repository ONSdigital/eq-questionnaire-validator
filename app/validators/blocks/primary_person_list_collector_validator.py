from app import error_messages
from app.validators.blocks import BlockValidator
from app.validators.blocks.validate_collector_quesitons_mixin import (
    ValidateCollectorQuestionsMixin,
)


class PrimaryPersonListCollectorValidator(
    BlockValidator, ValidateCollectorQuestionsMixin
):
    def validate(self):
        super(PrimaryPersonListCollectorValidator, self).validate()

        self._validate_primary_person_list_answer_references(self.block)

        collector_questions = self.questionnaire_schema.get_all_questions_for_block(
            self.block
        )

        self.validate_collector_questions(
            collector_questions,
            self.block["add_or_edit_answer"]["value"],
            error_messages.NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR,
            error_messages.NON_EXISTENT_PRIMARY_PERSON_LIST_COLLECTOR_ANSWER_VALUE,
        )

        self.validate_primary_person_list_collector_answer_ids(self.block)

    def _validate_primary_person_list_answer_references(self, block):
        main_answer_ids = self.questionnaire_schema.get_all_answer_ids(block["id"])

        if block["add_or_edit_answer"]["id"] not in main_answer_ids:
            self.add_error(
                error_messages.ADD_OR_EDIT_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK,
                referenced_id=block["add_or_edit_answer"]["id"],
            )

    def validate_primary_person_list_collector_answer_ids(self, block):
        """
        - Ensure that answer_ids on add blocks match between all blocks that populate a single list.
        """
        list_name = block["for_list"]

        add_or_edit_answer_ids = self.questionnaire_schema.get_all_answer_ids(
            block["add_or_edit_block"]["id"]
        )

        other_list_collectors = self.questionnaire_schema.get_other_blocks(
            self.block["id"], for_list=list_name, type="PrimaryPersonListCollector"
        )

        for other_list_collector in other_list_collectors:
            other_add_ids = self.questionnaire_schema.get_all_answer_ids(
                other_list_collector["add_or_edit_block"]["id"]
            )
            difference = other_add_ids.symmetric_difference(add_or_edit_answer_ids)
            if difference:
                self.add_error(
                    error_messages.NON_UNIQUE_ANSWER_ID_FOR_PRIMARY_LIST_COLLECTOR_ADD_OR_EDIT,
                    list_name=list_name,
                )
