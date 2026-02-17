"""This module contains the ValueSourceValidator class, which is responsible for validating value sources in a
questionnaire schema.

Classes:
    ValueSourceValidator
"""

from functools import cached_property

from app.validators.validator import Validator


class ValueSourceValidator(Validator):
    """Validator for value sources in a questionnaire schema.
    Note: A value source defines where a value is coming from, such as an answer, metadata, or progress reference.

    Attributes:
        value_source (dict): The value source to be validated, which includes the source type, identifier(s), and
        optional selector.
        json_path (str): The JSON path to the value source in the questionnaire schema, used for error context.
        questionnaire_schema (QuestionnaireSchema): The questionnaire schema containing the value source,
        used for validation against valid identifiers.
        parent_section (dict, optional): The parent section of the value source, used for validating progress
        source references.
        parent_block (dict, optional): The parent block of the value source, used for validating progress source
        references.

    Methods:
        _get_valid_progress_value_source_block_identifiers
        _get_valid_progress_value_source_section_identifiers
        block_ids_in_past_repeating_sections
        past_repeating_section_ids
        current_block_id
        future_block_ids
        past_block_ids
        future_section_ids
        current_section_id
        past_section_ids
        validate
        validate_source_reference
        _validate_source_reference
        _validate_progress_source_reference
        _validate_source_identifier_progress_source
        _validate_source_identifier
        _validate_answer_source_selector_reference
    """

    COMPOSITE_ANSWER_INVALID = "Invalid composite answer"
    COMPOSITE_ANSWER_FIELD_INVALID = "Invalid field for composite answer"
    SOURCE_REFERENCE_INVALID = "Invalid {} source reference"
    ANSWER_SOURCE_REFERENCE_INVALID = SOURCE_REFERENCE_INVALID.format("answers")

    # Progress source reference errors
    SOURCE_REFERENCE_CURRENT_BLOCK = (
        "Invalid {} source reference: the identifier being referenced "
        "in the progress source cannot be the current block"
    )
    SOURCE_REFERENCE_CURRENT_SECTION = (
        "Invalid {} source reference: the identifier being referenced "
        "in the progress source cannot be the current section"
    )
    SOURCE_REFERENCE_FUTURE_BLOCK = (
        "Invalid {} source reference: the identifier being referenced "
        "in the progress source must come before the current block"
    )
    SOURCE_REFERENCE_FUTURE_SECTION = (
        "Invalid {} source reference: the identifier being referenced "
        "in the progress source must come before the current section"
    )
    SOURCE_REFERENCE_BLOCK_IN_REPEATING_SECTION = (
        "Invalid {} source reference: the identifier being "
        "referenced in the progress source cannot be a block in a repeating section except for current section"
    )
    SOURCE_REFERENCE_REPEATING_SECTION = (
        "Invalid {} source reference: the identifier being referenced "
        "in the progress source cannot be a repeating section"
    )

    COMPOSITE_ANSWERS_TO_SELECTORS_MAP = {
        "Address": ["line1", "line2", "town", "postcode"],
    }
    RESPONSE_METADATA_IDENTIFIERS = ["started_at"]

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        value_source,
        json_path,
        questionnaire_schema,
        parent_section=None,
        parent_block=None,
    ):
        super().__init__(value_source)
        self.value_source = value_source
        self.questionnaire_schema = questionnaire_schema
        self.context["json_path"] = json_path
        self.parent_section = parent_section
        self.parent_block = parent_block

        self._valid_source_identifiers_map = {
            "answers": self.questionnaire_schema.answers_with_context,
            "metadata": self.questionnaire_schema.metadata_ids,
            "response_metadata": self.RESPONSE_METADATA_IDENTIFIERS,
            "list": self.questionnaire_schema.list_names,
            "calculated_summary": self.questionnaire_schema.calculated_summary_block_ids,
            "grand_calculated_summary": self.questionnaire_schema.grand_calculated_summary_block_ids,
        }

        if self.value_source["source"] == "progress":
            self._valid_source_identifiers_map["progress"] = {
                "block_ids": self._get_valid_progress_value_source_block_identifiers(),
                "section_ids": self._get_valid_progress_value_source_section_identifiers(),
            }

    def _get_valid_progress_value_source_block_identifiers(self):
        """Return a set of block ids that are before the current parent block and not in a repeating section except for
        the current section.
        """
        return self.past_block_ids - set([self.current_block_id]) - self.block_ids_in_past_repeating_sections

    def _get_valid_progress_value_source_section_identifiers(self):
        """Return a set of section ids that are before the current parent section and not in a repeating section except
        for the current section.
        """
        return self.past_section_ids - set([self.current_section_id]) - self.past_repeating_section_ids

    @cached_property
    def block_ids_in_past_repeating_sections(self) -> set[str]:
        """Return a set of block ids that are in repeating sections that are before the current parent section."""
        return {
            block["id"]
            for section_id in self.past_repeating_section_ids
            for block in self.questionnaire_schema.blocks_by_section_id[section_id]
        }

    @cached_property
    def past_repeating_section_ids(self) -> set:
        """Return a set of repeating section ids that are before the current parent section."""
        repeating_section_ids = set()
        for section_id in self.past_section_ids:
            if self.questionnaire_schema.is_repeating_section(section_id):
                repeating_section_ids.add(section_id)
        return repeating_section_ids

    @property
    def current_block_id(self) -> str | None:
        """Return the current block id if the value source is within a block, otherwise None."""
        if self.parent_block:
            return self.parent_block.get("id")
        return None

    @cached_property
    def future_block_ids(self) -> set[str]:
        """Return a set of block ids that are after the current parent block or in the current section if the current
        block is None."""
        return (
            set(self.questionnaire_schema.block_ids_without_sub_blocks)
            - self.past_block_ids
            - set([self.current_block_id])
        )

    @cached_property
    def past_block_ids(self) -> set[str]:
        """Return a set of block ids that are before the current parent block or in previous sections if the current."""
        if self.parent_block is None:
            # Progress value source is at section level.
            # Return all blocks in the previous sections, that aren't in a repeating section
            past_blocks_ids = {
                block["id"]
                for section_id in self.past_section_ids
                for block in self.questionnaire_schema.blocks_by_section_id[section_id]
            }
        else:
            parent_block_id = self.parent_block["id"]
            parent_block_index_in_block_list = self.questionnaire_schema.block_ids_without_sub_blocks.index(
                parent_block_id,
            )
            past_blocks_ids = set(
                self.questionnaire_schema.block_ids_without_sub_blocks[:parent_block_index_in_block_list],
            )

        return past_blocks_ids

    @cached_property
    def future_section_ids(self) -> set[str]:
        """Return a set of section ids that are after the current parent section."""
        return set(self.questionnaire_schema.section_ids) - self.past_section_ids - set([self.current_section_id])

    @cached_property
    def current_section_id(self) -> str | None:
        """Return the current section id if the value source is within a section, otherwise None."""
        return self.parent_section.get("id") if self.parent_section else None

    @cached_property
    def past_section_ids(self) -> set[str]:
        """Return a list of sections that are before the current parent section."""
        ids = set()
        if self.parent_section and (parent_section_id := self.parent_section.get("id")):
            parent_section_index_in_section_list = self.questionnaire_schema.section_ids.index(parent_section_id)
            ids = set(
                self.questionnaire_schema.section_ids[:parent_section_index_in_section_list],
            )
        return ids

    def validate(self):
        """Validate the value source by calling the 'validate_source_reference' method.

        Returns:
            A list of errors with context if any are found.
        """
        self.validate_source_reference()
        return self.errors

    def validate_source_reference(self):
        """Validate that the identifier or identifiers in the value source reference is/are valid for the specified
        source type by calling the appropriate validation method based on the source type.
        """
        source = self.value_source["source"]
        identifiers = self.value_source["identifier"]
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        if source == "progress":
            self._validate_progress_source_reference(identifiers)
        else:
            self._validate_source_reference(identifiers, source)

    def _validate_source_reference(self, identifiers, source):
        """Validate that the identifier or identifiers in the value source reference is/are valid for the specified
        source if its different source than 'progress'.

        Args:
            identifiers (list): A list of strings representing the identifier(s) being referenced in the value
            source (str): A string representing the source type of the value source, such as 'answers', 'metadata', etc.
        """
        valid_identifiers = self._valid_source_identifiers_map.get(source)
        if valid_identifiers is None:
            return

        for identifier in identifiers:
            self._validate_source_identifier(
                source,
                identifier=identifier,
                valid_identifiers=valid_identifiers,
            )

    def _validate_progress_source_reference(self, identifiers):
        """Validate that the identifier or identifiers in the value source reference is/are valid for the 'progress'
        source.

        Args:
            identifiers (list): A list of strings representing the identifier(s) being referenced in the value.
        """
        selector = self.value_source.get("selector")

        if selector == "block":
            valid_identifiers = self._valid_source_identifiers_map["progress"]["block_ids"]
        else:
            valid_identifiers = self._valid_source_identifiers_map["progress"]["section_ids"]

        for identifier in identifiers:
            self._validate_source_identifier_progress_source(
                selector=selector,
                identifier=identifier,
                valid_identifiers=valid_identifiers,
            )

    def _validate_source_identifier_progress_source(
        self,
        *,
        selector,
        identifier,
        valid_identifiers,
    ):
        """Detects & adds errors for invalid progress source references. Rules for valid progress source references are
        as follows:
        - Block must be before the current parent block.
        - Block must NOT be in a repeat section except if it is the current section.
        - Section must be before the current parent section.
        - Section must NOT be the parent section.
        - Section must NOT be a repeat section.

        Args:
            selector (str): A string representing the selector in the value source, which indicates whether the
            progress reference is to a block or a section.
            identifier (str): A string representing the identifier being referenced in the value source.
            valid_identifiers (dict): A dict of valid identifiers for the progress source reference.
        """
        if identifier not in valid_identifiers:
            error_mapping = {
                "block": {
                    tuple([self.current_block_id]): self.SOURCE_REFERENCE_CURRENT_BLOCK,
                    tuple(self.future_block_ids): self.SOURCE_REFERENCE_FUTURE_BLOCK,
                    tuple(
                        self.block_ids_in_past_repeating_sections,
                    ): self.SOURCE_REFERENCE_BLOCK_IN_REPEATING_SECTION,
                },
                "section": {
                    tuple(
                        [self.current_section_id],
                    ): self.SOURCE_REFERENCE_CURRENT_SECTION,
                    tuple(
                        self.future_section_ids,
                    ): self.SOURCE_REFERENCE_FUTURE_SECTION,
                    tuple(
                        self.past_repeating_section_ids,
                    ): self.SOURCE_REFERENCE_REPEATING_SECTION,
                },
            }
            for error_identifiers, error_message in error_mapping[selector].items():
                if identifier in error_identifiers:
                    self.add_error(
                        error_message.format("progress"),
                        identifier=identifier,
                    )
                    return

            self.add_error(
                self.SOURCE_REFERENCE_INVALID.format("progress"),
                identifier=identifier,
            )

    def _validate_source_identifier(self, source, *, identifier, valid_identifiers):
        """Detects & adds errors for invalid source references for sources other than 'progress'.

        Args:
            source (str): A string representing the source type of the value source, such as 'answers', 'metadata', etc.
            identifier (str): A string representing the identifier being referenced in the value source.
            valid_identifiers (dict): A dictionary of valid identifiers for the specified.
        """
        if identifier not in valid_identifiers:
            self.add_error(
                self.SOURCE_REFERENCE_INVALID.format(source),
                identifier=identifier,
            )

        elif source == "answers" and (selector := self.value_source.get("selector")):
            self._validate_answer_source_selector_reference(identifier, selector)

    def _validate_answer_source_selector_reference(self, identifier, selector):
        """Validate that the selector in an answer source value source is valid for the type of the answer being
        referenced.

        Args:
            identifier (str): A string representing the identifier of the answer being referenced in the value source.
            selector (str): A string representing the selector in the value source.
        """
        answers_with_context = self.questionnaire_schema.answers_with_context
        answer_type = answers_with_context[identifier]["answer"]["type"]

        if answer_type not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP:
            self.add_error(self.COMPOSITE_ANSWER_INVALID, identifier=identifier)

        elif selector not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP[answer_type]:
            self.add_error(self.COMPOSITE_ANSWER_FIELD_INVALID, identifier=identifier)
