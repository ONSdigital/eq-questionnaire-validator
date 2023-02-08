import re

from eq_translations.survey_schema import SurveySchema

from app import error_messages
from app.validators.answer_code_validator import AnswerCodeValidator
from app.validators.metadata_validator import MetadataValidator
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import QuestionnaireSchema, find_duplicates
from app.validators.sections.section_validator import SectionValidator
from app.validators.validator import Validator


class QuestionnaireValidator(Validator):
    def __init__(self, schema_element=None):
        super().__init__(schema_element)

        self.questionnaire_schema = QuestionnaireSchema(schema_element)

    def validate(self):
        metadata_validator = MetadataValidator(
            self.schema_element["metadata"],
            self.schema_element["theme"],
        )
        self.errors += metadata_validator.validate()

        placeholder_validator = PlaceholderValidator(self.schema_element)
        self.errors += placeholder_validator.validate()

        self.validate_duplicates()
        self.validate_smart_quotes()

        for section in self.questionnaire_schema.sections:
            section_validator = SectionValidator(section, self.questionnaire_schema)
            self.errors += section_validator.validate()

        required_hub_section_ids = self.schema_element["questionnaire_flow"][
            "options"
        ].get("required_completed_sections", [])

        self.validate_required_section_ids(
            self.questionnaire_schema.section_ids, required_hub_section_ids
        )

        if answer_codes := self.schema_element.get("answer_codes"):
            answer_code_validator = AnswerCodeValidator(
                data_version=self.schema_element["data_version"],
                answer_codes=answer_codes,
                questionnaire_schema=self.questionnaire_schema,
            )
            self.errors += answer_code_validator.validate()

        return self.errors

    def validate_required_section_ids(self, section_ids, required_section_ids):

        for required_section_id in required_section_ids:
            if required_section_id not in section_ids:
                self.add_error(
                    error_messages.REQUIRED_HUB_SECTION_UNDEFINED,
                    required_section_id=required_section_id,
                )

    def validate_duplicates(self):
        for duplicate in find_duplicates(self.questionnaire_schema.ids):
            self.add_error(error_messages.DUPLICATE_ID_FOUND, id=duplicate)

    def validate_referred_numeric_answer(self, answer, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        if answer_ranges[answer.get("id")]["min"] is None:
            self.add_error(
                error_messages.ANSWER_REFERENCE_CANNOT_BE_USED_ON_MIN,
                reference_id=answer["minimum"]["value"]["identifier"],
                answer_id=answer["id"],
            )
        if answer_ranges[answer.get("id")]["max"] is None:
            self.add_error(
                error_messages.ANSWER_REFERENCE_CANNOT_BE_USED_ON_MAX,
                reference_id=answer["maximum"]["value"]["identifier"],
                answer_id=answer["id"],
            )

    def validate_smart_quotes(self):

        schema_object = SurveySchema(self.schema_element)

        # pylint: disable=invalid-string-quote
        quote_regex = re.compile(r"['|\"]+(?![^{]*})+(?![^<]*>)")

        for translatable_item in schema_object.translatable_items:
            schema_text = translatable_item.value

            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for schema_text in values_to_check:
                if schema_text and quote_regex.search(schema_text):
                    self.add_error(
                        error_messages.DUMB_QUOTES_FOUND,
                        pointer=translatable_item.pointer,
                    )
