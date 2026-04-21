"""This module contains the top level questionnaire validator which is responsible for validating rules that apply to
the whole questionnaire schema and calling the section validator for each section in the questionnaire.

Classes:
    QuestionnaireValidator
"""
import html.entities
import re
from eq_translations.survey_schema import SurveySchema
from collections.abc import Mapping

from app import error_messages
from app.validators.answer_code_validator import AnswerCodeValidator
from app.validators.metadata_validator import MetadataValidator
from app.validators.placeholders.placeholder_validator import PlaceholderValidator
from app.validators.questionnaire_schema import (
    QuestionnaireSchema,
    find_duplicates,
    get_block_by_answer_id,
    get_blocks,
    get_object_containing_key,
)
from app.validators.sections.section_validator import SectionValidator
from app.validators.translatable_items import get_translatable_items
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


class QuestionnaireValidator(Validator):
    """This is the top level validator for a questionnaire schema. It validates the generic questionnaire schema rules
    (preview questions, smart quotes, spacing) and order of references but also calls the placeholder validator and
    section validator for each section in the questionnaire.

    Attributes:
        schema_element (Mapping): The entire questionnaire schema to be validated.

    Methods:
        validate
        validate_required_section_ids
        validate_duplicates
        validate_referred_numeric_answer
        validate_smart_quotes
        validate_white_spaces
        validate_introduction_block
        validate_answer_references
        validate_list_references
        resolve_source_block_id
    """

    def __init__(self, schema_element=None):
        super().__init__(schema_element)

        self.questionnaire_schema = QuestionnaireSchema(schema_element)

    def validate(self):
        """Validate the questionnaire schema by calling various validation methods for different aspects of the schema,
        such as metadata, placeholders, duplicates and instantiating placeholder and section validators.

        Returns:
            A list of error messages if validation fails, or an empty list if validation passes.
        """
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
        self.validate_html()
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
        """Validate that all required section ids specified in the questionnaire flow options are defined in the
        sections of the questionnaire schema.

        Args:
            section_ids (list): A list of section ids defined in the questionnaire schema.
            required_section_ids (list): A list of required section ids specified in the questionnaire flow options.
        """
        for required_section_id in required_section_ids:
            if required_section_id not in section_ids:
                self.add_error(
                    error_messages.REQUIRED_HUB_SECTION_UNDEFINED,
                    required_section_id=required_section_id,
                )

    def validate_duplicates(self):
        """Validate that there are no duplicate ids in the questionnaire schema. Calls the find_duplicates function
        from the questionnaire_schema module.
        """
        for duplicate in find_duplicates(self.questionnaire_schema.ids):
            self.add_error(error_messages.DUPLICATE_ID_FOUND, id=duplicate)

    def validate_referred_numeric_answer(self, answer, answer_ranges):
        """Validate that if an answer has a minimum or maximum value that is a reference to another answer, then the
        answer being referred to must be of a numeric type and must appear earlier in the schema.

        Args:
            answer (dict): The answer being validated, which may contain minimum and maximum value references.
            answer_ranges (dict): A dictionary mapping answer ids to their minimum and maximum value types.
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
        """Validate that there are no single and double "dumb" quotes in the translatable text fields of the
        questionnaire schema. Uses a regular expression to search for occurrences of dumb quotes in the text.
        """
        quote_regex = re.compile(r"['|\"]+(?![^{]*})+(?![^<]*>)")

        for translatable_item in get_translatable_items(self.schema_element):  # type: ignore
            # Schema object always exists at this point
            schema_text = translatable_item.value
            # not needed after eq-translations update
            translatable_item.pointer = translatable_item.pointer.replace("(", "").replace(")", "")

            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for schema_text in values_to_check:
                if isinstance(schema_text, str) and schema_text and quote_regex.search(schema_text):
                    self.add_error(
                        error_messages.DUMB_QUOTES_FOUND,
                        pointer=translatable_item.pointer,
                    )
    def validate_html(self):
        # loop over translatable strings
        # call check_html_tags(text, pointer)

        schema_object = SurveySchema(self.schema_element)

        for translatable_item in schema_object.translatable_items:
            schema_text = translatable_item.value
            values_to_check = [schema_text]

            if isinstance(schema_text, dict):
                values_to_check = schema_text.values()

            for text in values_to_check:
                if not isinstance(text, str) or not text:
                    continue

                if "<" in text and ">" in text:
                    self.check_html_tags(text, translatable_item.pointer)

                if "&" in text and ";" in text:
                    self.check_html_entities(text, translatable_item.pointer)          

        return

    def check_html_tags(self, text, pointer):
        """Checks valid html tags.

        Args:
            text (str): The text to be validated for HTML tags.
            pointer (str): The JSON pointer indicating the location of the text in the questionnaire schema, used for
            error reporting.
        """

        allowed_tags = {"p", "strong", "a", "b"}
        self_closing_tags = {"br"}
        
        tag_matches = re.finditer(r"</?([a-zA-Z0-9]+)[^>]*>", text)
        stack = [] 
        
        for match in tag_matches: #for each HTML tag found in the text
            raw_tag = match.group(0)
            tag_name = match.group(1).lower()

            is_closing = raw_tag.startswith("</")
            is_self_closing = raw_tag.endswith("/>") or tag_name in self_closing_tags

            if tag_name not in allowed_tags: # invalid html tag found
                self.add_error(
                    error_messages.HTML_FOUND,
                    pointer=pointer,
                    text=text,
                )
                return
            
            if is_closing: #closed tag found, pop
                if tag_name in self_closing_tags or not stack or stack[-1] != tag_name:
                    self.add_error(
                        error_messages.HTML_FOUND,
                        pointer=pointer,
                        text=text,
                    )
                    return

                stack.pop()

            elif not is_self_closing:#open tag not void elem
                stack.append(tag_name)

        if stack:
            self.add_error(
                error_messages.HTML_FOUND,
                pointer=pointer,
                text=text,
            )

    
    def is_valid_html_entity(self, entity):
        # Numeric entity
        if entity.startswith("&#") and entity.endswith(";"):
            numeric = entity[2:-1]

            try:
                if numeric.lower().startswith("x"):
                    codepoint = int(numeric[1:], 16)
                else:
                    codepoint = int(numeric)
            except ValueError:
                return False

            return 0 <= codepoint <= 0x10FFFF

        # Named entity
        if entity.startswith("&") and entity.endswith(";"):
            return entity[1:-1] in html.entities.html5

        return False
    
    def check_html_entities(self, text, pointer):
        entity_matches = re.findall(r"&[^;\s]+;", text)

        for entity in entity_matches:
            if not self.is_valid_html_entity(entity):
                self.add_error(
                    error_messages.HTML_ENTITIES_FOUND,
                    pointer=pointer,
                    text=text,
                )
                return 

    def validate_white_spaces(self):
        """Validate that there are no leading, trailing or multiple consecutive white spaces in the translatable text
        of the questionnaire schema.
        """
        for translatable_item in get_translatable_items(self.schema_element):  # type: ignore
            # Schema object always exists at this point
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
        """Validate if introduction block is present when preview questions are enabled."""
        blocks = get_blocks(self.questionnaire_schema)
        has_introduction_blocks = any(block["type"] == "Introduction" for block in blocks)
        if not has_introduction_blocks:
            self.add_error(error_messages.PREVIEW_WITHOUT_INTRODUCTION_BLOCK)

    def validate_answer_references(self):
        """Validate that all answer references in the questionnaire schema refer to answers that are defined earlier
        in the schema.
        """
        # Handling blocks in group
        for group in self.questionnaire_schema.groups:
            self.validate_answer_source_group(group)

        # Handling section level "enabled" rule
        for index, section in enumerate(self.questionnaire_schema.sections):
            self.validate_answer_source_section(section, index)

    def validate_answer_source_group(self, group):
        """Validate that all answer references in a group refer to answers that are defined earlier in the schema.

        Args:
            group (dict): The group to validate, which may contain blocks with answer references.
        """
        identifier_references = get_object_containing_key(group, "source")
        for path, identifier_reference, parent_block in identifier_references:
            # set up default parent_block_id for later check (group or block level)
            parent_block_id = None
            if "source" in identifier_reference and identifier_reference["source"] == "answers":
                source_block = get_block_by_answer_id(
                    self.questionnaire_schema,
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
        return None

    def validate_answer_source_section(self, section, section_index):
        """Validates that all answer references in a section's "enabled" rule refer to answers that are defined earlier
        in the schema.

        Args:
            section (dict): The section to validate, which may contain an "enabled" rule with answer references.
            section_index (int): The index of the section in the questionnaire schema, used to determine the order of
            sections for validation.
        """
        identifier_references = get_object_containing_key(section, "source")
        for path, identifier_reference, _ in identifier_references:
            if "source" in identifier_reference and identifier_reference["source"] == "answers" and "enabled" in path:
                source_block = get_block_by_answer_id(
                    self.questionnaire_schema,
                    identifier_reference["identifier"],
                )
                if (
                    isinstance(source_block, dict)
                    and (source_block_id := self.resolve_source_block_id(source_block))
                    and (
                        source_block_section_id := self.questionnaire_schema.get_section_id_for_block_id(
                            source_block_id,
                        )
                    )
                    and (
                        source_block_section_index := self.questionnaire_schema.get_section_index_for_section_id(
                            source_block_section_id,
                        )
                    )
                    and section_index < source_block_section_index
                ):
                    self.add_error(
                        error_messages.ANSWER_REFERENCED_BEFORE_EXISTS.format(
                            answer_id=identifier_reference["identifier"],
                        ),
                        section_id=section["id"],
                    )

    def resolve_source_block_id(self, source_block: Mapping) -> str:
        """Resolve the block id of a source block, handling cases where the source block is nested within a list
        collector.

        Args:
            source_block: The block that is being referenced as a source for an answer.

        Returns:
            The block id of the source block, which is the id of a parent list collector.
        """
        # Handling of source block nested (list collector's add-block)
        if (
            source_block["type"] == "ListAddQuestion"
            and isinstance(source_block, dict)
            and (
                block_id := self.questionnaire_schema.get_parent_list_collector_for_add_block(
                    source_block["id"],
                )
            )
        ):
            return block_id

        # Handling of source block nested (list collector's repeating block)
        if (
            source_block["type"] == "ListRepeatingQuestion"
            and isinstance(source_block, dict)
            and (
                block_id := self.questionnaire_schema.get_parent_list_collector_for_repeating_block(
                    source_block["id"],
                )
            )
        ):
            return block_id
        # Handling of standard source block
        return source_block["id"]

    def validate_list_references(self):
        """Validates that all list references in the questionnaire schema refer to lists that are defined earlier in
        the schema.
        """
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
