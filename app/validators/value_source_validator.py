"""The ValueSourceValidator validates the value source of a block."""

from functools import cached_property

from app.validators.validator import Validator


class ValueSourceValidator(Validator):
    """The ValueSourceValidator validates the value source of a block."""
    COMPOSITE_ANSWER_INVALID = "Invalid composite answer"
    COMPOSITE_ANSWER_FIELD_INVALID = "Invalid field for composite answer"
    SOURCE_REFERENCE_INVALID = "Invalid {} source reference"
    ANSWER_SOURCE_REFERENCE_INVALID = SOURCE_REFERENCE_INVALID.format("answers")

    # Progress source reference errors
    SOURCE_REFERENCE_CURRENT_BLOCK = "Invalid {} source reference: the identifier being referenced in the progress source cannot be the current block"
    SOURCE_REFERENCE_CURRENT_SECTION = "Invalid {} source reference: the identifier being referenced in the progress source cannot be the current section"
    SOURCE_REFERENCE_FUTURE_BLOCK = "Invalid {} source reference: the identifier being referenced in the progress source must come before the current block"
    SOURCE_REFERENCE_FUTURE_SECTION = "Invalid {} source reference: the identifier being referenced in the progress source must come before the current section"
    SOURCE_REFERENCE_BLOCK_IN_REPEATING_SECTION = (
        "Invalid {} source reference: the identifier being "
        "referenced in the progress source cannot be a block in a repeating section except for current section"
    )
    SOURCE_REFERENCE_REPEATING_SECTION = "Invalid {} source reference: the identifier being referenced in the progress source cannot be a repeating section"

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
        """The ValueSourceValidator validates the value source of a block."""
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
        return (
            self.past_block_ids
            - set(self.current_block_id)
            - self.block_ids_in_past_repeating_sections
        )

    def _get_valid_progress_value_source_section_identifiers(self):
        return (
            self.past_section_ids
            - set(self.current_section_id)
            - self.past_repeating_section_ids
        )

    @cached_property
    def block_ids_in_past_repeating_sections(self) -> set[str]:
        """Returns a list of block IDs that are in repeating sections that are before the current parent section."""
        return {
            block["id"]
            for section_id in self.past_repeating_section_ids
            for block in self.questionnaire_schema.blocks_by_section_id[section_id]
        }

    @cached_property
    def past_repeating_section_ids(self) -> set[str]:
        """Returns a list of repeating sections' IDs that are before the current parent section."""
        return {
            section_id
            for section_id in self.past_section_ids
            if self.questionnaire_schema.is_repeating_section(section_id)
        }

    @property
    def current_block_id(self) -> str | None:
        """Returns the ID of the current parent block if it exists."""
        if self.parent_block:
            return self.parent_block.get("id")

    @cached_property
    def future_block_ids(self) -> set[str]:
        """Returns a list of block IDs that are after the current parent block."""
        return (
            set(self.questionnaire_schema.block_ids_without_sub_blocks)
            - self.past_block_ids
            - set(self.current_block_id)
        )

    @cached_property
    def past_block_ids(self) -> set[str]:
        """Returns a list of block IDs that are before the current parent block."""
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
            parent_block_index_in_block_list = (
                self.questionnaire_schema.block_ids_without_sub_blocks.index(
                    parent_block_id,
                )
            )
            past_blocks_ids = set(
                self.questionnaire_schema.block_ids_without_sub_blocks[
                    :parent_block_index_in_block_list
                ],
            )

        return past_blocks_ids

    @cached_property
    def future_section_ids(self) -> set[str]:
        """Returns a list of section IDs that are after the current parent section."""
        return (
            set(self.questionnaire_schema.section_ids)
            - self.past_section_ids
            - set(self.current_section_id)
        )

    @cached_property
    def current_section_id(self) -> str | None:
        """Returns the ID of the current parent section if it exists."""
        if self.parent_section:
            return self.parent_section.get("id")

    @cached_property
    def past_section_ids(self) -> set[dict]:
        """Returns a list of sections that are before the current parent section."""
        parent_section_id = self.parent_section["id"]
        parent_section_index_in_section_list = (
            self.questionnaire_schema.section_ids.index(parent_section_id)
        )
        ids = set(
            self.questionnaire_schema.section_ids[:parent_section_index_in_section_list],
        )

        return ids

    def validate(self):
        """Validates the value source."""
        self.validate_source_reference()
        return self.errors

    def validate_source_reference(self):
        """Validates the value source reference."""
        source = self.value_source["source"]
        identifiers = self.value_source["identifier"]
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        if source == "progress":
            self._validate_progress_source_reference(identifiers)
        else:
            self._validate_source_reference(identifiers, source)

    def _validate_source_reference(self, identifiers, source):
        valid_identifiers = self._valid_source_identifiers_map.get(source)
        if valid_identifiers is None:
            return

        for identifier in identifiers:
            self._validate_source_identifier(
                source, identifier=identifier, valid_identifiers=valid_identifiers,
            )

    def _validate_progress_source_reference(self, identifiers):
        selector = self.value_source.get("selector")

        if selector == "block":
            valid_identifiers = self._valid_source_identifiers_map["progress"][
                "block_ids"
            ]
        else:
            valid_identifiers = self._valid_source_identifiers_map["progress"][
                "section_ids"
            ]

        for identifier in identifiers:
            self._validate_source_identifier_progress_source(
                selector=selector,
                identifier=identifier,
                valid_identifiers=valid_identifiers,
            )

    def _validate_source_identifier_progress_source(
        self, *, selector, identifier, valid_identifiers,
    ):
        """Detects & adds errors for invalid progress source references.

        - Block must be before the current parent block
        - Block must NOT be in a repeat section except if it is the current section
        - Section must be before the current parent section
        - Section must NOT be the parent section
        - Section must NOT be a repeat section
        """
        if identifier not in valid_identifiers:
            error_mapping = {
                "block": {
                    tuple(self.current_block_id): self.SOURCE_REFERENCE_CURRENT_BLOCK,
                    tuple(self.future_block_ids): self.SOURCE_REFERENCE_FUTURE_BLOCK,
                    tuple(
                        self.block_ids_in_past_repeating_sections,
                    ): self.SOURCE_REFERENCE_BLOCK_IN_REPEATING_SECTION,
                },
                "section": {
                    tuple(
                        self.current_section_id,
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
                        error_message.format("progress"), identifier=identifier,
                    )
                    return

            self.add_error(
                self.SOURCE_REFERENCE_INVALID.format("progress"),
                identifier=identifier,
            )

    def _validate_source_identifier(self, source, *, identifier, valid_identifiers):
        if identifier not in valid_identifiers:
            self.add_error(
                self.SOURCE_REFERENCE_INVALID.format(source),
                identifier=identifier,
            )

        elif source == "answers" and (selector := self.value_source.get("selector")):
            self._validate_answer_source_selector_reference(identifier, selector)

    def _validate_answer_source_selector_reference(self, identifier, selector):
        answers_with_context = self.questionnaire_schema.answers_with_context
        answer_type = answers_with_context[identifier]["answer"]["type"]

        if answer_type not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP:
            self.add_error(self.COMPOSITE_ANSWER_INVALID, identifier=identifier)

        elif selector not in self.COMPOSITE_ANSWERS_TO_SELECTORS_MAP[answer_type]:
            self.add_error(self.COMPOSITE_ANSWER_FIELD_INVALID, identifier=identifier)
