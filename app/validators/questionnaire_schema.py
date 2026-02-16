# pylint: disable=too-many-public-methods,too-many-lines
"""This module provides the `QuestionnaireSchema` class, which is responsible for parsing a questionnaire schema.
It extracts and organizes the various components of the schema, such as sections, blocks, groups, answers, and lists.

Classes:
    QuestionnaireSchema
Functions:
    find_duplicates
    find_dictionary_duplicates
    get_object_containing_key
    get_parent_block_from_match
    get_element_value
    json_path_position
    get_context_from_match
"""
import collections
import re
from collections import defaultdict
from functools import cached_property, lru_cache
from typing import Iterable, Mapping, TypeVar

from jsonpath_ng import parse
from jsonpath_ng.ext import parse as ext_parse

from app.answer_type import AnswerType

MAX_NUMBER = 999_999_999_999_999
MIN_NUMBER = -999_999_999_999_999
MAX_DECIMAL_PLACES = 6

T = TypeVar("T")
K = TypeVar("K")


def find_duplicates(values: Iterable[T]) -> list[T]:
    """Find duplicate values in an iterable.

    Args:
        values: An iterable of values to check for duplicates.

    Returns:
        A list of duplicate values.
    """
    return [item for item, count in collections.Counter(values).items() if count > 1]


def find_dictionary_duplicates(dictionary: dict[K, T]) -> list[K]:
    """Find keys with duplicate values.

    Args:
        dictionary: A dictionary to check for duplicate values.

    Returns:
        A list of keys that have duplicate values.
    """
    value_counts = collections.Counter(dictionary.values())
    return [key for key, value in dictionary.items() if value_counts[value] > 1]


def get_object_containing_key(data, key_name):
    """Get all dicts that contain `key_name` within a piece of data.

    Args:
        data (dict): The data to search through, an object representing the questionnaire schema.
        key_name (str): The key name to search for within the data.

    Returns:
        matches (list): A list of tuples, where each tuple contains the JSON path to the matched object.
    """
    matches = []
    for match in parse(f"$..{key_name}").find(data):
        parent_block = get_parent_block_from_match(match)
        matches.append((str(match.full_path), match.context.value, parent_block))
    return matches


def get_parent_block_from_match(match) -> dict | None:
    """Given a jsonpath_ng match object, walk up the context until we find the parent block
    (the first context with 'blocks' in its value) and return that block.

    Args:
        match (jsonpath_ng.match): A jsonpath_ng match object representing a match for a key in the schema.

    Returns:
        block (dict): The parent block containing the matched key, or None if no block is found.
    """
    walked_contexts = [match.context]

    while walked_contexts[-1] is not None:
        current_context = walked_contexts[-1]
        if "blocks" not in current_context.value:
            walked_contexts.append(current_context.context)
        else:
            break

    # No block found and reached top of JSON file
    if walked_contexts[-1] is None:
        return None

    block = walked_contexts[-3].value

    return block


def get_element_value(key, match):
    """Given a key and a jsonpath_ng match, return the value of the element that matches the key within the context.

    Args:
        key (str): The key to search for within the context of the match.
        match (jsonpath_ng.match): A jsonpath_ng match object representing a match for a key in the schema.

    Returns:
        match.value (jsonpath_ng.match.value, jsonpath_ng.match): if the match is for the key,
        otherwise continue walking up the context until we find a match for the key or reach the top of the JSON file.
    """
    if str(match.full_path.left).endswith(f".{key}") or str(match.full_path.left) == key:
        return match.value
    return get_element_value(key, match.context)


def json_path_position(match) -> tuple[int, ...]:
    """Given a match, whose json path will look like 'sections[x].groups[y].blocks[z]...' return a tuple
    of (x, y, z, ...) to represent the position of the match within the schema.

    Args:
        match (jsonpath_ng.match): A jsonpath_ng match object representing a match for a key in the schema.

    Returns:
        tuple: A tuple to represent the position of the match within the schema.
    """
    path = str(match.full_path)
    indices = re.findall(r"\[(\d+)]", path)
    return tuple(int(index) for index in indices)


def get_context_from_match(match):
    """Given a match, return a dictionary containing the section id, block id and group id that the match is within.

    Args:
        match (jsonpath_ng.match): A jsonpath_ng match object representing a match for a key in the schema.

    Returns:
        dict: A dictionary containing the section id, block id and group id that the match is within.
    """
    full_path = str(match.full_path)
    section = get_element_value("sections", match)
    block = (
        get_element_value("repeating_blocks", match)
        if "repeating_blocks" in full_path
        else get_element_value("blocks", match)
    )
    block_id = block["id"]
    group = get_element_value("groups", match)

    for sub_block in ["add_block", "edit_block", "add_or_edit_block", "remove_block"]:
        if sub_block in full_path and sub_block in block:
            block_id = block[sub_block]["id"]

    return {"section": section["id"], "block": block_id, "group_id": group["id"]}


class QuestionnaireSchema:
    """The class parses and organizes a questionnaire schema from json, organises schema elements like sections, blocks,
    groups, answers, lists, and related metadata.
    It provides methods to access and process these elements for validation purposes.

    Attributes:
        schema (dict): The original questionnaire schema as a dictionary.

    Methods:
        get_block_ids_for_block_type
        list_names_by_dynamic_answer_id
        numeric_answer_ranges
        metadata_ids
        questions_with_context
        answers_with_context
        lists_with_context
        capture_answers
        ids
        id_paths
        answer_id_to_option_values_map
        answers
        get_answer
        get_answer_type
        get_group
        get_section
        get_block
        get_blocks
        get_other_blocks
        has_single_driving_question
        get_all_questions_for_block
        get_list_collector_answer_ids
        get_list_collector_answer_ids_by_child_block
        get_all_answer_ids
        get_all_dynamic_answer_ids
        get_list_name_for_answer_id
        get_calculation_block_ids
        get_answer_ids_for_value_source
        is_repeating_section
        get_parent_section_for_block
        get_parent_list_collector_for_add_block
        get_parent_list_collector_for_repeating_block
        is_block_in_repeating_section
        get_numeric_value_for_value_source
        get_answers_from_question
        get_section_block_ids
        get_section_id_for_block
        get_section_id_for_block_id
        get_section_index_for_section_id

    """

    def __init__(self, schema):
        self.schema = schema
        self.matches = [
            *parse("$..blocks[*]").find(self.schema),
            *parse("$..[add_block, edit_block, add_or_edit_block, remove_block]").find(
                self.schema,
            ),
            *parse("$..repeating_blocks[*]").find(self.schema),
        ]
        # order the blocks by the order that they occur in the json schema
        self.sorted_matches = sorted(self.matches, key=json_path_position)
        self.blocks = [match.value for match in self.sorted_matches]
        self.blocks_by_id = {block["id"]: block for block in self.blocks}
        self.block_ids = list(self.blocks_by_id.keys())
        self.block_ids_without_sub_blocks = [block["id"] for block in self.blocks]
        self.calculated_summary_block_ids = self.get_block_ids_for_block_type(
            "CalculatedSummary",
        )
        self.grand_calculated_summary_block_ids = self.get_block_ids_for_block_type(
            "GrandCalculatedSummary",
        )
        self.sections = [match.value for match in ext_parse("$.sections[*]").find(self.schema)]
        self.sections_by_id = {section["id"]: section for section in self.sections}
        self.section_ids = list(self.sections_by_id.keys())
        self.blocks_by_section_id = {
            section["id"]: [block for group in section["groups"] for block in group["blocks"]]
            for section in self.sections
        }

        self.groups = [match.value for match in ext_parse("$..groups[*]").find(self.schema)]
        self.groups_by_id = {group["id"]: group for group in self.groups}
        self.group_ids = list(self.groups_by_id.keys())

        self.supplementary_lists = [
            match.value for match in ext_parse("$..supplementary_data.lists[*]").find(self.schema)
        ]
        self.list_collectors = [
            match.value
            for match in ext_parse('$..blocks[?(@.type=="ListCollector")]').find(
                self.schema,
            )
        ]
        self.list_collector_names = [list_collector["for_list"] for list_collector in self.list_collectors]
        self.list_names = self.list_collector_names + self.supplementary_lists
        self.list_names_by_repeating_block_id = {
            block["id"]: list_collector["for_list"]
            for list_collector in self.list_collectors
            for block in list_collector.get("repeating_blocks", [])
        }
        self._answers_with_context = {}
        self._lists_with_context = {}

    @lru_cache
    def get_block_ids_for_block_type(self, block_type: str) -> list[str]:
        """Get a list of block ids for a given block type.

        Args:
            block_type: The type of block to get the ids for.

        Returns:
            list: A list of block ids for the given block type.
        """
        return [block["id"] for block in self.blocks if block["type"] == block_type]

    @cached_property
    def list_names_by_dynamic_answer_id(self) -> dict[str, str]:
        """Get a mapping of dynamic answer id to list name for all dynamic answers that source from a list.

        Returns:
            dict: A dictionary mapping dynamic answer ids to list names.
        """
        answer_id_to_list: dict[str, str] = {}
        for dynamic_answer in ext_parse("$..dynamic_answers[*]").find(self.schema):
            dynamic_answer = dynamic_answer.value
            if dynamic_answer["values"]["source"] == "list":
                list_name = dynamic_answer["values"]["identifier"]
                answer_id_to_list.update(
                    {answer["id"]: list_name for answer in dynamic_answer["answers"]},
                )
        return answer_id_to_list

    @cached_property
    def numeric_answer_ranges(self):
        """Get a mapping of answer id to its numeric range values, used for extracting minimum and maximum values for
        percentage, currency, unit and number answer types.

        Returns:
            numeric_answer_ranges (dict): A dictionary mapping answer ids to key-value pairs,
            where the keys are 'min', 'max', 'decimal_places', 'min_referred', 'max_referred' and 'default'.
        """
        numeric_answer_ranges = {}

        for answer in ext_parse("$..answers[*]").find(self.schema):
            numeric_answer_ranges[answer.value["id"]] = self._get_numeric_range_values(
                answer.value,
                numeric_answer_ranges,
            )

        return numeric_answer_ranges

    @cached_property
    def metadata_ids(self):
        """ "Get a list of metadata ids used in the schema's top-level metadata field.

        Returns:
            list: A list of metadata ids or empty list.
        """
        if "metadata" in self.schema:
            return [m["name"] for m in self.schema["metadata"]]
        return []

    @cached_property
    def questions_with_context(self):
        """Get a list of tuples of question objects with their context by calling 'get_context_from_match'.

        Returns:
            list: A list of tuples, where each tuple contains a question object and its context
            (section id, block id and group id).
        """
        return [
            (match.value, get_context_from_match(match))
            for match in parse("$..question").find(self.schema)
            if isinstance(match.value, dict)
        ]

    @property
    def answers_with_context(self):
        """Gets a dictionary of every answer in a questionnaire schema as answer ids mapped to answer with context
        object pairs by calling 'capture_answers' to extract the answers. Updates the _answers_with_context instance
        attribute of the class.

        Returns:
            dict: A dictionary mapping answer ids to their answer objects with context, where the context includes
            the section id, block id and group id that the answer is within.
        """
        if self._answers_with_context:
            return self._answers_with_context

        answers_dict = {}
        for question, context in self.questions_with_context:
            self.capture_answers(
                answers=self.get_answers_from_question(question),
                answers_dict=answers_dict,
                context=context,
            )

        self._answers_with_context = answers_dict
        return self._answers_with_context

    @answers_with_context.setter
    def answers_with_context(self, value):
        """Setter for answers_with_context to allow setting the value of _answers_with_context from outside the class,
        used for testing purposes.

        Args:
            value (dict): A dictionary mapping answer ids to their answer objects with context,
            where the context includes the section id, block id and group id that the answer is within.
        """
        self._answers_with_context = value

    @property
    def lists_with_context(self):
        """Gets a dictionary of list ids mapped to the context (section_index, block_index), handles them diffently
        depending on which list collector type is used for that list.

        Returns:
            dict: A dictionary (instance attribute) mapping list ids to their context, where the context includes
            section index and block index
        """
        if supplementary_list := self.supplementary_lists:
            for list_id in supplementary_list:
                self._lists_with_context[list_id] = {
                    "section_index": 0,
                    "block_index": 0,
                }

        if blocks := self.list_collectors:
            for block in blocks:
                list_id = block["for_list"]
                if list_id not in self._lists_with_context:
                    section_id = self.get_section_id_for_block_id(block["id"])
                    section_index = self.section_ids.index(section_id)
                    self._lists_with_context[list_id] = {
                        "section_index": section_index,
                        "block_index": self.block_ids.index(block["id"]),
                    }
        if blocks := self.get_blocks(type="PrimaryPersonListCollector"):
            for block in blocks:
                list_id = block["for_list"]
                if list_id not in self._lists_with_context or (
                    self.block_ids.index(block["id"]) < self._lists_with_context[list_id]["block_index"]
                ):
                    section_id = self.get_section_id_for_block_id(block["id"])
                    section_index = self.section_ids.index(section_id)
                    self._lists_with_context[list_id] = {
                        "section_index": section_index,
                        "block_index": self.block_ids.index(block["id"]),
                    }

        return self._lists_with_context

    @staticmethod
    def capture_answers(*, answers, answers_dict, context):
        """Capture answers and their context into a dictionary for a given question.

        Args:
            answers (list): A list of answer objects to capture.
            answers_dict (dict): A dictionary to store the captured answers.
            context (dict): A dictionary containing the context to associate with each answer.
        """
        for answer in answers:
            answers_dict[answer["id"]] = {"answer": answer, **context}
            for option in answer.get("options", []):
                detail_answer = option.get("detail_answer")
                if detail_answer:
                    answers_dict[detail_answer["id"]] = {
                        "answer": detail_answer,
                        **context,
                    }

    @cached_property
    def ids(self):
        """Capture all ids, including block ids, question ids, answer ids, group ids and section ids,
        with the following rules:
            - within a block, ids can be duplicated across variants, but must still be unique outside of the block.
            - answer ids must be duplicated across (add / edit) blocks on list collectors which populate the same list.

        Returns:
            all_ids (list): A list of all unique ids used in the schema.
        """
        unique_ids_per_block = defaultdict(set)
        all_block_ids = []
        non_block_ids = []
        all_ids = []

        for path, value in self.id_paths:
            if "blocks" in path:
                # Generate a string path and add it to the set representing the ids in that path
                path_list = path.split(".")
                is_block_id = len(path_list) == 6
                if is_block_id:
                    all_block_ids.append(value)
                else:
                    block_path = path_list[: path_list.index("blocks") + 2]

                    string_path = ".".join(block_path)
                    # Since unique_ids_per_block is a set, the duplicate ids will be only recorded the first time
                    # they appear within the block.
                    unique_ids_per_block[string_path].add(value)
            else:
                non_block_ids.append(value)

        for block_ids in unique_ids_per_block.values():
            all_ids.extend(block_ids)

        all_ids.extend(non_block_ids)
        all_ids.extend(all_block_ids)

        return all_ids

    @cached_property
    def id_paths(self):
        """Function that generates paths for id values will be returned with the json path to them through the object.

        Example:
            'sections.[0].groups[0].blocks[1].question_variants[0].question.question-2'

        Yields:
            Path and value tuple for all ids in the schema excluding routing rules,
            skip conditions, 'when' rules.
        """
        ignored = ["routing_rules", "skip_conditions", "when"]

        # Ignore duplicate answer_ids within multiple list collector blocks
        ignored_sub_paths = [
            "edit_block",
            "add_or_edit_block",
            "add_block",
            "remove_block",
        ]

        for match in parse("$..id").find(self.schema):
            full_path = str(match.full_path)
            is_list_collector_answer_id = False
            if hasattr(match.context.context.full_path, "left"):
                is_list_collector_answer_id = (
                    any(ignored_sub_path in full_path for ignored_sub_path in ignored_sub_paths)
                    and str(match.context.context.full_path.right) == "answers"
                )
            if not any(ignored_path in full_path for ignored_path in ignored) and not is_list_collector_answer_id:
                yield str(match.full_path.left), match.value

    @cached_property
    def answer_id_to_option_values_map(self):
        """Get a mapping of answer id to the set of option values for that answer, used for validating that option label
        from value. Only for answers that have options.

        Returns:
            answer_id_to_option_values_map (dict): A dictionary mapping answer ids to the set of option values for
            that answer.
        """
        answer_id_to_option_values_map = defaultdict(set)

        for answer in self.answers:
            if "options" not in answer:
                continue

            answer_id = answer["id"]
            option_values = [option["value"] for option in answer["options"]]

            answer_id_to_option_values_map[answer_id].update(option_values)

        return answer_id_to_option_values_map

    @cached_property
    def answers(self):
        """A generator function that yields answers from all questions with context.

        This method iterates over all questions with their context and retrieves
        the answers associated with each question using the `get_answers_from_question` method.

        Yields:
            The answers block extracted from each question in `questions_with_context`.
        """
        for question, _ in self.questions_with_context:
            yield from self.get_answers_from_question(question)

    @lru_cache
    def get_answer(self, answer_id):
        """Get an answer by its id.
        Args: answer_id (str): The id of the answer to retrieve.

        Returns:
            dict: The answer block associated with the provided answer_id.
        """
        return self.answers_with_context[answer_id]["answer"]

    @lru_cache
    def get_answer_type(self, answer_id):
        """Get the type of an answer by its id.

        Args:
            answer_id (str): The id of the answer to retrieve the type for.

        Returns:
            AnswerType: The type of the answer associated with the provided answer_id.
        """
        answer = self.get_answer(answer_id)
        return AnswerType(answer["type"])

    @lru_cache
    def get_group(self, group_id):
        """Get a top-level group block (inside section block) by its id.

        Args:
            group_id (str): The id of the group to retrieve.

        Returns:
            dict: The group block associated with the provided group_id.
        """
        return self.groups_by_id[group_id]

    @lru_cache
    def get_section(self, section_id):
        """Get a section block by its id.

        Args:
            section_id (str): The id of the section to retrieve.

        Returns:
            dict: The section block associated with the provided section_id.
        """
        return self.sections_by_id[section_id]

    @lru_cache
    def get_block(self, block_id):
        """Get any block by its id.

        Args:
            block_id (str): The id of the block to retrieve.

        Returns:
            dict: The block associated with the provided block_id, or None if no block is found.
        """
        return self.blocks_by_id.get(block_id, None)

    @lru_cache
    def get_blocks(self, **filters):
        """Get all blocks that match the given filters. Filters are passed as keyword arguments where the key is the
        field to filter on and the value is the value to match. This will return either a list of blocks or
        an empty list. If no filters are provided, all blocks will be returned.

        Example:
            get_blocks(type="ListCollector", for_list="household") will return all blocks of type ListCollector
            that have a for_list value of household.

        Args:
            **filters: Arbitrary keyword arguments representing the fields and values to filter the blocks by.

        Returns:
            list: A list of blocks that match the given filters, or an empty list if no blocks match.
        """
        conditions = []
        for key, value in filters.items():
            conditions.append(f'@.{key}=="{value}"')

        if conditions:
            final_condition = " & ".join(conditions)
            return [
                match.value
                for match in ext_parse(f"$..blocks[?({final_condition})]").find(
                    self.schema,
                )
            ]
        return self.blocks

    @lru_cache
    def get_other_blocks(self, block_id_to_filter, **filters):
        """Get all blocks that match the given filters excluding the block given in block_id_to_filter.

        Example:
            get_other_blocks(block_id_to_filter="list-collector", type="ListCollector", for_list="household")
            will return all blocks of type ListCollector that have a for_list value of household except for
            the block with id list-collector.

        Args:
            block_id_to_filter (str): The id of the block to exclude from the results.
            **filters: Arbitrary keyword arguments representing the fields and values to filter the blocks by.

        Returns:
            list: A list of blocks that match the given filters except for the block with the given block_id_to_filter,
            or an empty list if no blocks match.
        """
        conditions = []
        for key, value in filters.items():
            conditions.append(f'@.{key}=="{value}"')

        if conditions:
            final_condition = " & ".join(conditions)
            return [
                match.value
                for match in ext_parse(
                    f'$..blocks[?(@.id != "{block_id_to_filter}" & {final_condition})]',
                ).find(self.schema)
            ]
        return self.blocks

    @lru_cache
    def has_single_driving_question(self, list_name):
        """Check if a list collector has only one driving question.

        Args:
            list_name (str): The name of the list to check for a single driving question.

        Returns:
            bool: True if there is only one driving question for the list collector with the given list name,
            False otherwise.
        """
        return (
            len(
                self.get_blocks(
                    type="ListCollectorDrivingQuestion",
                    for_list=list_name,
                ),
            )
            == 1
        )

    @staticmethod
    def get_all_questions_for_block(block):
        """Get all questions on a block including variants.
        Args: block (dict): The block to get the questions for.

        Returns:
            questions (list): A list of all question objects in the block, including variants.
        """
        questions = []

        for variant in block.get("question_variants", []):
            questions.append(variant["question"])

        single_question = block.get("question")
        if single_question:
            questions.append(single_question)

        return questions

    @lru_cache
    def get_list_collector_answer_ids(self, block_id):
        """Get all answer IDs for a list collector block.

        Args:
            block_id (str): The id of the list collector block to get the answer ids for.

        Returns:
            set: A set of all answer ids associated with the list collector block, including those in add,
            edit and add_or_edit blocks.
        """
        block = self.blocks_by_id[block_id]
        if "add_or_edit_block" in block:
            return self.get_all_answer_ids(block["add_or_edit_block"]["id"])

        add_answer_ids = self.get_all_answer_ids(block["add_block"]["id"])

        edit_answer_ids = self.get_all_answer_ids(block["edit_block"]["id"])
        return add_answer_ids | edit_answer_ids

    @lru_cache
    def get_list_collector_answer_ids_by_child_block(self, block_id: str):
        """Retrieves the answer ids associated with the child blocks of a given list collector block.

        Args:
            block_id (str): The ID of the list collector block.

        Returns:
            dict: A dictionary where the keys are child block types ("add_block", "edit_block", "remove_block") and the
            values are lists of answer ids associated with each child block.
        """
        block = self.blocks_by_id[block_id]
        return {
            child_block: self.get_all_answer_ids(block[child_block]["id"])
            for child_block in ["add_block", "edit_block", "remove_block"]
        }

    @lru_cache
    def get_all_answer_ids(self, block_id):
        """Get all answer ids for a block including variants.

        Args:
            block_id (str): The id of the block to get the answer ids for.

        Returns:
            set: A set of all answer ids in the block, including variants.
        """
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return {answer["id"] for question in questions for answer in self.get_answers_from_question(question)}

    @lru_cache
    def get_all_dynamic_answer_ids(self, block_id):
        """Get all dynamic answer ids for a block including variants.

        Args:
            block_id (str): The id of the block to get the dynamic answer ids for.
        Returns: set: A set of all dynamic answer ids in the block, including variants.
        """
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return {
            answer["id"] for question in questions for answer in question.get("dynamic_answers", {}).get("answers", [])
        }

    def get_list_name_for_answer_id(self, answer_id: str) -> str | None:
        """Get list name for answer id.

        Args:
            answer_id (str): The id of the answer to get the list name for.

        Returns:
            str: The name of the list that answer repeats over if the answer is dynamic or in a repeating block
            or section, otherwise None.
        """
        if list_name := self.list_names_by_dynamic_answer_id.get(answer_id):
            return list_name
        if block := self.get_block_by_answer_id(answer_id):
            if list_name := self.list_names_by_repeating_block_id.get(block["id"]):
                return list_name
            if block["type"] == "ListCollector":
                return block["for_list"]
            section = self.get_parent_section_for_block(block["id"])
            if section and section.get("repeat"):
                return section["repeat"]["for_list"]
        return None

    @lru_cache
    def get_first_answer_in_block(self, block_id):
        """Get the first answer id in a block.

        Args:
            block_id (str): The id of the block to get the first answer id for.

        Returns:
            str: The id of the first answer in the block.
        """
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return self.get_answers_from_question(questions[0])[0]

    @lru_cache
    def get_block_id_by_answer_id(self, answer_id):
        """Get the block id for a given answer id by iterating through all questions with context.

        Args:
            answer_id (str): The id of the answer to get the block id for.

        Returns:
            block_id (str): The id of the block that the answer with the given answer_id is in, or None.
        """
        for question, context in self.questions_with_context:
            if block_id := self.get_block_id_for_answer(
                answer_id=answer_id,
                answers=self.get_answers_from_question(question),
                context=context,
            ):
                return block_id

    @staticmethod
    def get_block_id_for_answer(*, answer_id, answers, context):
        """Get the block id for a given answer id by checking if the answer id matches any of the answers.

        Args:
            answer_id (str): The id of the answer to get the block id for.
            answers (list): A list of answer objects to check for a match with the answer_id.
            context (dict): A dictionary containing the context to return if a match is found, including the block id.

        Returns:
            str: The id of the block that the answer with the given answer_id is in, or None if no block is found.
        """
        for answer in answers:
            if answer_id == answer["id"]:
                return context["block"]
            for option in answer.get("options", []):
                detail_answer = option.get("detail_answer")
                if detail_answer and answer_id == detail_answer["id"]:
                    return context["block"]

    @lru_cache
    def get_block_by_answer_id(self, answer_id):
        """Get the block for a given answer id by first getting the block id using get_block_id_by_answer_id and
        then returning the entire block.

        Args:
            answer_id (str): The id of the answer to get the block for.

        Returns:
            dict: The block that the answer with the given answer_id is in, or None if no block is found.
        """
        block_id = self.get_block_id_by_answer_id(answer_id)

        return self.get_block(block_id)

    def _get_numeric_range_values(self, answer, answer_ranges):
        """ "Get the numeric range values for a given answer, including minimum and maximum values,
        decimal places and whether the minimum and maximum values are exclusive. If the minimum or maximum value
        is a reference to another answer, the reference will be resolved to the actual value of that answer using
        get_numeric_value_for_value_source.

        Args:
            answer (dict): The answer to get the numeric range values for.
            answer_ranges (dict): A dictionary mapping answer ids to their numeric range values, used for
            resolving references
        Returns:
            dict: A dictionary containing the numeric range values for the given answer, including minimum and maximum
        """
        min_value = answer.get("minimum", {}).get("value", {})
        max_value = answer.get("maximum", {}).get("value", {})
        min_referred = min_value.get("identifier") if isinstance(min_value, dict) else None
        max_referred = max_value.get("identifier") if isinstance(max_value, dict) else None

        exclusive = answer.get("exclusive", False)
        decimal_places = answer.get("decimal_places", 0)

        return {
            "min": self._get_answer_minimum(
                min_value,
                decimal_places,
                exclusive,
                answer_ranges,
            ),
            "max": self._get_answer_maximum(
                max_value,
                decimal_places,
                exclusive,
                answer_ranges,
            ),
            "decimal_places": decimal_places,
            "min_referred": min_referred,
            "max_referred": max_referred,
            "default": answer.get("default"),
        }

    def _get_answer_minimum(
        self,
        defined_minimum,
        decimal_places,
        exclusive,
        answer_ranges,
    ):
        """Get the minimum value for a given answer, resolving references if necessary and adjusting for exclusivity.

        Args:
            defined_minimum (int, dict): The defined minimum value for the answer, which can be a direct
            numeric value or a reference to another answer. Could never be a string since this method is only used for
            number validators.
            decimal_places (int): The number of decimal places for the answer, used for adjusting the minimum value
            if it is exclusive.
            exclusive (bool): A flag indicating whether the minimum value is exclusive, which determines how the minimum
            value is adjusted.
            answer_ranges (dict): A dictionary mapping answer ids to their numeric range values, used for resolving
            references.

        Returns:
            minimum_value (int): The resolved minimum value for the answer, adjusted for exclusivity if necessary.
        """
        minimum_value = self._get_numeric_value(defined_minimum, 0, answer_ranges)
        if exclusive:
            return minimum_value + (1 / 10**decimal_places)
        return minimum_value

    def _get_answer_maximum(
        self,
        defined_maximum,
        decimal_places,
        exclusive,
        answer_ranges,
    ):
        """Get the maximum value for a given answer, resolving references if necessary and adjusting for exclusivity.

        Args:
            defined_maximum (int, dict): The defined maximum value for the answer, which can be a direct
            numeric value or a reference to another answer. Could never be a string since this method is only used for
            number validators.
            decimal_places (int): The number of decimal places for the answer, used for adjusting the maximum value
            exclusive (bool): A flag indicating whether the maximum value is exclusive, which determines how the maximum
            value is adjusted.
            answer_ranges (dict): A dictionary mapping answer ids to their numeric range values
        Returns:
            maximum_value (int): The resolved maximum value for the answer, adjusted for exclusivity if necessary.
        """
        maximum_value = self._get_numeric_value(
            defined_maximum,
            MAX_NUMBER,
            answer_ranges,
        )
        if exclusive:
            return maximum_value - (1 / 10**decimal_places)
        return maximum_value

    def _get_numeric_value(self, defined_value, system_default, answer_ranges):
        """Get a numeric value, resolving references if necessary. If the defined value is a reference to
        another answer, the reference will be resolved to the actual value of that answer using
        get_numeric_value_for_value_source. If the reference cannot be resolved to a valid numeric value,
        the system default will be returned.

        Args:
            defined_value (int, str, dict): The defined value, which can be a direct numeric value or a reference
            to another answer.
            system_default (int): The default value to return if the defined value is a reference that cannot be
            resolved to a valid numeric value.
            answer_ranges (dict): A dictionary mapping answer ids to their numeric
            range values, used for resolving references.

        Returns:
            defined_value (int) or system_default (int): The resolved numeric value for the defined value, or the
            system default if the defined value is a reference that cannot be resolved to a valid numeric value.
        """
        if not isinstance(defined_value, dict):
            return defined_value
        if defined_value.get("source"):
            referred_answer = self.get_numeric_value_for_value_source(
                value_source=defined_value,
                answer_ranges=answer_ranges,
            )
            # Referred answer is not valid (picked up by _validate_referred_numeric_answer)
            if not referred_answer:
                return None
        return system_default

    @staticmethod
    def get_calculation_block_ids(*, block: Mapping, source_type: str) -> list[str]:
        """This method extracts block ids from a calculation object within a given block. It can be used to retrieve
        answers for a calculated summary or calculated summaries for a grand calculated summary.

        Args:
            block: The block containing the calculation object.
            source_type: The type of source to filter the block IDs (e.g., "answers" or "calculated_summary").

        Returns:
            A list of block ids of type source_type used in a calculation object.
        """
        if block["calculation"].get("answers_to_calculate"):
            return block["calculation"]["answers_to_calculate"]

        value_sources = get_object_containing_key(
            block["calculation"]["operation"],
            "source",
        )

        return [source[1]["identifier"] for source in value_sources if source[1]["source"] == source_type]

    def get_answer_ids_for_value_source(
        self,
        value_source: Mapping[str, str],
    ) -> list[str]:
        """Gets the list of answer_ids relating to the provided value source. Either the identifier if its an answer
        source or the list of included answer ids in the case of a calculated or grand calculated summary.

        Args:
            value_source: A dictionary representing the value source, containing a 'source' key indicating the type of
            source (e.g., 'answers', 'calculated_summary') and an 'identifier' key indicating the specific identifier
            for the source.

        Returns:
            A list of answer ids associated with the value source, or a list containing the identifier if the source
            is not a calculated summary or grand calculated summary.
        """
        source = value_source["source"]
        identifier = value_source["identifier"]
        if block := self.get_block(identifier):
            if source == "calculated_summary":
                return self.get_calculation_block_ids(
                    block=block,
                    source_type="answers",
                )
            if source == "grand_calculated_summary":
                identifiers = []
                for calculated_summary_id in self.get_calculation_block_ids(
                    block=block,
                    source_type="calculated_summary",
                ):
                    if calculated_summary_block := self.get_block(calculated_summary_id):
                        answer_ids = self.get_calculation_block_ids(
                            block=calculated_summary_block,
                            source_type="answers",
                        )
                        identifiers.extend(answer_ids)
                return identifiers
        return [identifier]

    def is_repeating_section(self, section_id: str) -> bool:
        """Check if a section is a repeating section by checking if it has a repeat key in its definition.

        Args:
            section_id (str): The id of the section to check.

        Returns:
            bool: True if the section is a repeating section, False otherwise.
        """
        return "repeat" in self.sections_by_id[section_id]

    def get_parent_section_for_block(self, block_id) -> dict | None:
        """Get the parent section for a given block id by iterating through the blocks in each section and checking
        for a match
        Args:
            block_id (str): The id of the block to get the parent section for.

        Returns:
            dict, None: The section that the block with the given block_id is in, or None if no section is found.
        """
        for section_id, blocks in self.blocks_by_section_id.items():
            for block in blocks:
                if block_id == block["id"]:
                    return self.sections_by_id[section_id]
        return None

    def get_parent_list_collector_for_add_block(self, block_id) -> str | None:
        """Get the parent list collector block id for a given add block id by iterating through the blocks
        in each section and checking for a match with the add block id.

        Args:
            block_id (str): The id of the add block to get the parent list collector for.

        Returns:
            str, None: The id of the list collector block that the add block with the given block_id is in,
            or None if no list collector block is found.
        """
        for blocks in self.blocks_by_section_id.values():
            for block in blocks:
                if block["type"] == "ListCollector" and block["add_block"]["id"] == block_id:
                    return block["id"]
        return None

    def get_parent_list_collector_for_repeating_block(self, block_id) -> str | None:
        """Get the parent list collector block id for a given repeating block id by iterating through the blocks
        Args:
            block_id (str): The id of the repeating block to get the parent list collector for.

        Returns:
            The id of the list collector block that the repeating block with the given block_id is in,
            or None if no list collector block is found.
        """
        for blocks in self.blocks_by_section_id.values():
            for block in blocks:
                if block["type"] in [
                    "ListCollector",
                    "ListCollectorContent",
                ] and block.get("repeating_blocks"):
                    for repeating_block in block["repeating_blocks"]:
                        if repeating_block["id"] == block_id:
                            return block["id"]
        return None

    def is_block_in_repeating_section(self, block_id: str) -> bool:
        """Check if a block is in a repeating section by first getting the parent section for the block and
        then checking
        Args:
            block_id: The id of the block to check.

        Returns:
            bool: True if the block is in a repeating section, False otherwise.
        """
        parent_section = self.get_parent_section_for_block(block_id)
        if parent_section:
            return self.is_repeating_section(parent_section["id"])
        return False

    def get_numeric_value_for_value_source(
        self,
        *,
        value_source: Mapping[str, str],
        answer_ranges: Mapping[str, Mapping],
    ) -> Mapping | None:
        """Get the numeric value for a given value source by first getting the answer ids associated with the value
        source using.

        Args:
            value_source: A dictionary representing the value source, containing a 'source' key indicating
            the type of source (e.g., 'answers', 'calculated_summary') and an 'identifier' key indicating the specific
            identifier for the source.
            answer_ranges: A dictionary mapping answer ids to their numeric range values, used
            for resolving references.

        Returns:
            referred_answer, None: A dictionary containing the numeric range values for the answer(s) associated
            with the value source, or None if any of the answers cannot be resolved to valid numeric values.
        """
        referred_answer = None
        answers_to_calculate = self.get_answer_ids_for_value_source(value_source)
        for answer_id in answers_to_calculate:
            referred_answer = answer_ranges.get(answer_id)
            if referred_answer is None:
                return None
        return referred_answer

    @staticmethod
    def get_answers_from_question(question):
        """Get all answers from a question, including dynamic answers.

        Args:
            question (dict): The question to get the answers from.

        Returns:
            list: A list of all answer objects in the question, including dynamic answers.
        """
        return [
            *question.get("dynamic_answers", {}).get("answers", []),
            *question.get("answers", []),
        ]

    def get_section_block_ids(self, current_section=None):
        """Retrieves the list of block IDs for a given section.

        Args:
            current_section (str, None): The id of the section for which block ids are to be retrieved.

        Returns:
            list: A list of block ids associated with the specified section.
        """
        return [block["id"] for block in self.blocks_by_section_id[current_section]]

    def get_section_id_for_block(self, block: Mapping) -> str | None:
        """Get the section id for a given block by iterating through the blocks in each section and checking for
        a match with the given block.

        Args:
            block: The block to get the section id for.

        Returns:
            section_id: The id of the section that the block is in, or None if no section is found.
        """
        for section_id, blocks in self.blocks_by_section_id.items():
            if block in blocks:
                return section_id
        return None

    def get_section_id_for_block_id(self, block_id: str) -> str | None:
        """Get the section id for a given block id by first getting the block using get_block and then using
        get_section_id_for_block.

        Args:
            block_id: The id of the block to get the section id for.

        Returns:
            section_id: The id of the section that the block with the given block_id is in.
        """
        if block := self.get_block(block_id):
            return self.get_section_id_for_block(block)
        return None

    def get_section_index_for_section_id(self, section_id: str) -> int | None:
        """Get the section index for a given section id by iterating through the sections and checking for a match
        with the given section id.

        Args:
            section_id: The id of the section to get the index for.

        Returns:
            section_index: The index of the section with the given section_id.
        """
        for index, section in enumerate(self.sections):
            if section["id"] == section_id:
                return index
        return None
