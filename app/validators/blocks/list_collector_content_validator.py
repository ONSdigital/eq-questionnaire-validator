from app.error_messages import FOR_LIST_NEVER_POPULATED
from app.validators.blocks.block_validator import BlockValidator


class ListCollectorContentValidator(BlockValidator):
    def validate(self):
        super().validate()
        self.validate_for_list_is_valid()
        return self.errors

    def validate_for_list_is_valid(self):
        """Validates that the 'for_list' property is valid.

        Verifies that the list for the list collector content block is either:
        1) Populated by a standard list collector - OR
        2) In the supplementary data lists property so populated by supplementary data
        """
        list_name = self.block["for_list"]
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(
                FOR_LIST_NEVER_POPULATED,
                list_name=list_name,
            )
