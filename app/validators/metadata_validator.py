from functools import cached_property

from app.validators.questionnaire_schema import find_duplicates
from app.validators.validator import Validator


class MetadataValidator(Validator):
    MISSING_METADATA = "Metadata not specified in metadata field"
    DUPLICATE_METADATA = "Metadata contains duplicates"

    def __init__(self, metadata, theme_name, form_type=None):
        self.theme_name = theme_name
        self.form_type = form_type
        super().__init__(metadata)

    def validate(self):
        self.validate_duplicates()
        self.validate_mandatory()
        return self.errors

    @cached_property
    def metadata_names(self):
        return [metadata_field["name"] for metadata_field in self.schema_element]

    def validate_duplicates(self):
        duplicates = find_duplicates(self.metadata_names)

        if len(duplicates) > 0:
            self.add_error(self.DUPLICATE_METADATA, duplicates=duplicates)

    def validate_mandatory(self):
        # user_id and period_id required downstream for receipting
        # ru_name required for template rendering in business, default and NI theme
        # display_address required for template rendering in census, census-nisra theme when form_type exists
        required_metadata_names = []

        if self.theme_name in ["business", "default", "northernireland"]:
            required_metadata_names.extend(["user_id", "period_id", "ru_name"])
        elif self.theme_name in ["census", "census-nisra"]:
            if self.form_type:
                required_metadata_names.extend(
                    ["user_id", "period_id", "display_address"]
                )
            else:
                required_metadata_names.extend(["user_id", "period_id"])

        for metadata_name in required_metadata_names:
            if metadata_name not in self.metadata_names:
                self.add_error(self.MISSING_METADATA, metadata=metadata_name)
