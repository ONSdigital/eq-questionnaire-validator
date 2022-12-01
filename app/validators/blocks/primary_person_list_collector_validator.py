from app.validators.blocks.block_validator import BlockValidator
from app.validators.blocks.validate_list_collector_quesitons_mixin import (
    ValidateListCollectorQuestionsMixin,
)


class PrimaryPersonListCollectorValidator(
    BlockValidator, ValidateListCollectorQuestionsMixin
):
    REDIRECT_TO_LIST_ADD_BLOCK = "RedirectToListAddBlock"
    NO_REDIRECT_TO_LIST_ADD_BLOCK = f"{REDIRECT_TO_LIST_ADD_BLOCK} action not found"
    NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR = (
        "The primary person list collector block does not contain a Radio answer type"
    )
    NON_UNIQUE_ANSWER_ID_FOR_PRIMARY_LIST_COLLECTOR_ADD_OR_EDIT = (
        "Multiple primary person list collectors "
        "populate a list using different answer ids in the add_or_edit block"
    )

    def validate(self):
        super().validate()

        collector_questions = self.questionnaire_schema.get_all_questions_for_block(
            self.block
        )
        self.validate_collector_questions(
            collector_questions,
            self.NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR,
            self.REDIRECT_TO_LIST_ADD_BLOCK,
            self.NO_REDIRECT_TO_LIST_ADD_BLOCK,
        )
        answer_ids = self.questionnaire_schema.get_list_collector_answer_ids(
            self.block["id"]
        )
        self.validate_same_name_answer_ids(answer_ids)

        self.validate_primary_person_list_collector_answer_ids(self.block)
        return self.errors

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
                    self.NON_UNIQUE_ANSWER_ID_FOR_PRIMARY_LIST_COLLECTOR_ADD_OR_EDIT,
                    list_name=list_name,
                )
