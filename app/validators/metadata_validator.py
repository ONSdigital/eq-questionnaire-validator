from functools import cached_property

from app.validators.questionnaire_schema import find_duplicates
from app.validators.validator import Validator


class MetadataValidator(Validator):
    MISSING_METADATA = "Metadata not specified in metadata field"
    DUPLICATE_METADATA = "Metadata contains duplicates"

    def __init__(self, metadata, theme_name):
        self.theme_name = theme_name
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
        required_metadata_names = []

        if self.theme_name in [
            "business",
            "default",
            "northernireland",
            "beis",
            "beis-ni",
            "orr",
        ]:
            required_metadata_names.extend(["user_id", "period_id", "ru_name"])

        for metadata_name in required_metadata_names:
            if metadata_name not in self.metadata_names:
                self.add_error(self.MISSING_METADATA, metadata=metadata_name)
