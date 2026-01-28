import re
from collections.abc import Mapping

from eq_translations.survey_schema import SurveySchema

from app import error_messages
from app.validators.answer_code_validator import AnswerCodeValidator
from app.validators.metadata_validator import MetadataValidator
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    find_duplicates,
    get_object_containing_key,
)
from app.validators.sections.section_validator import SectionValidator
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


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
        self.validate_white_spaces()
        self.validate_answer_references()
        self.validate_list_references()

        for section in self.questionnaire_schema.sections:
            section_validator = SectionValidator(section, self.questionnaire_schema)
            self.errors += section_validator.validate()

        required_hub_section_ids = self.schema_element["questionnaire_flow"]["options"].get(
            "required_completed_sections",
            [],
        )

        self.validate_required_section_ids(
            self.questionnaire_schema.section_ids,
            required_hub_section_ids,
        )

        if self.schema_element.get("preview_questions"):
            self.validate_introduction_block()

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
        """Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema.

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

        quote_regex = re.compile(r"['|\"]+(?![^{]*})+(?![^<]*>)")

        for translatable_item in schema_object.translatable_items:
            schema_text = translatable_item.value

            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for schema_text in values_to_check:
                if isinstance(schema_text, str) and schema_text and quote_regex.search(schema_text):
                    self.add_error(
                        error_messages.DUMB_QUOTES_FOUND,
                        pointer=translatable_item.pointer,
                    )

    def validate_white_spaces(self):
        schema_object = SurveySchema(self.schema_element)

        for translatable_item in schema_object.translatable_items:
            schema_text = translatable_item.value
            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for text in values_to_check:
                if isinstance(text, str) and (text.startswith(" ") or text.endswith(" ") or "  " in text):
                    self.add_error(
                        error_messages.INVALID_WHITESPACE_FOUND,
                        pointer=translatable_item.pointer,
                        text=text,
                    )

    def validate_introduction_block(self):
        blocks = self.questionnaire_schema.get_blocks()
        has_introduction_blocks = any(block["type"] == "Introduction" for block in blocks)
        if not has_introduction_blocks:
            self.add_error(error_messages.PREVIEW_WITHOUT_INTRODUCTION_BLOCK)

    def validate_answer_references(self):
        # Handling blocks in group
        for group in self.questionnaire_schema.groups:
            self.validate_answer_source_group(group)

        # Handling section level "enabled" rule
        for index, section in enumerate(self.questionnaire_schema.sections):
            self.validate_answer_source_section(section, index)

    def validate_answer_source_group(self, group):
        identifier_references = get_object_containing_key(group, "source")
        for path, identifier_reference, parent_block in identifier_references:
            # set up default parent_block_id for later check (group or block level)
            parent_block_id = None
            if "source" in identifier_reference and identifier_reference["source"] == "answers":
                source_block = self.questionnaire_schema.get_block_by_answer_id(
                    identifier_reference["identifier"],
                )
                # Handling non-existing blocks used as source
                if not source_block:
                    self.add_error(
                        ValueSourceValidator.ANSWER_SOURCE_REFERENCE_INVALID,
                        identifier=identifier_reference["identifier"],
                    )
                    return False
                # Handling block level answer sources (skipping group level)
                if parent_block and "blocks" in path:
                    parent_block_id = parent_block["id"]
                    parent_block_index = self.questionnaire_schema.block_ids.index(
                        parent_block_id,
                    )
                else:
                    # Handling group level skip conditions
                    first_block_id_in_group = group["blocks"][0]["id"]
                    parent_block_index = self.questionnaire_schema.block_ids.index(
                        first_block_id_in_group,
                    )

                source_block_id = self.resolve_source_block_id(source_block)

                source_block_index = self.questionnaire_schema.block_ids.index(
                    source_block_id,
                )
                if source_block_index > parent_block_index:
                    if parent_block_id:
                        self.add_error(
                            error_messages.ANSWER_REFERENCED_BEFORE_EXISTS.format(
                                answer_id=identifier_reference["identifier"],
                            ),
                            block_id=parent_block_id,
                        )
                    else:
                        self.add_error(
                            error_messages.ANSWER_REFERENCED_BEFORE_EXISTS.format(
                                answer_id=identifier_reference["identifier"],
                            ),
                            group_id=group["id"],
                        )

    def validate_answer_source_section(self, section, section_index):
        identifier_references = get_object_containing_key(section, "source")
        for path, identifier_reference, _ in identifier_references:
            if "source" in identifier_reference and identifier_reference["source"] == "answers" and "enabled" in path:
                source_block = self.questionnaire_schema.get_block_by_answer_id(
                    identifier_reference["identifier"],
                )
                if isinstance(source_block, dict) and (source_block_id := self.resolve_source_block_id(source_block)):
                    if source_block_section_id := self.questionnaire_schema.get_section_id_for_block_id(
                        source_block_id,
                    ):
                        source_block_section_index = self.questionnaire_schema.get_section_index_for_section_id(
                            source_block_section_id,
                        )
                        if source_block_section_index and section_index < source_block_section_index:
                            self.add_error(
                                error_messages.ANSWER_REFERENCED_BEFORE_EXISTS.format(
                                    answer_id=identifier_reference["identifier"],
                                ),
                                section_id=section["id"],
                            )

    def resolve_source_block_id(self, source_block: Mapping) -> str:
        # Handling of source block nested (list collector's add-block)
        if source_block["type"] == "ListAddQuestion":
            if isinstance(source_block, dict) and (
                block_id := self.questionnaire_schema.get_parent_list_collector_for_add_block(
                    source_block["id"],
                )
            ):
                return block_id

        # Handling of source block nested (list collector's repeating block)
        if source_block["type"] == "ListRepeatingQuestion":
            if isinstance(source_block, dict) and (
                block_id := self.questionnaire_schema.get_parent_list_collector_for_repeating_block(
                    source_block["id"],
                )
            ):
                return block_id
        # Handling of standard source block
        return source_block["id"]

    def validate_list_references(self):
        lists_with_context = self.questionnaire_schema.lists_with_context

        # We need to keep track of section index for: common_definitions.json#/section_enabled
        for section_index, section in enumerate(self.questionnaire_schema.sections):
            identifier_references = get_object_containing_key(section, "source")
            for _, identifier_reference, parent_block in identifier_references:
                if identifier_reference["source"] == "list":
                    list_identifier = identifier_reference["identifier"]
                    if parent_block:
                        if (
                            self.questionnaire_schema.block_ids.index(
                                parent_block["id"],
                            )
                            < lists_with_context[list_identifier]["block_index"]
                        ):
                            self.add_error(
                                error_messages.LIST_REFERENCED_BEFORE_CREATED.format(),
                                list_id=list_identifier,
                                section_id=section["id"],
                                block_id=parent_block["id"],
                            )
                    elif section_index < lists_with_context[list_identifier]["section_index"]:
                        # Section level "enabled" rule that can use
                        # list source, check: common_definitions.json#/section_enabled
                        self.add_error(
                            error_messages.LIST_REFERENCED_BEFORE_CREATED.format(),
                            list_name=list_identifier,
                            section_id=section["id"],
                        )
