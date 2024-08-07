# pylint: disable=too-many-public-methods
import collections
import re
from collections import defaultdict
from functools import cached_property, lru_cache
from typing import Iterable, Mapping, TypeVar

import jsonpath_rw_ext as jp
from jsonpath_rw import parse

from app.answer_type import AnswerType

MAX_NUMBER = 999_999_999_999_999
MIN_NUMBER = -999_999_999_999_999
MAX_DECIMAL_PLACES = 6

T = TypeVar("T")
K = TypeVar("K")


def find_duplicates(values: Iterable[T]) -> list[T]:
    return [item for item, count in collections.Counter(values).items() if count > 1]


def find_dictionary_duplicates(dictionary: dict[K, T]) -> list[K]:
    """
    Find keys with duplicate values
    """
    value_counts = collections.Counter(dictionary.values())
    return [key for key, value in dictionary.items() if value_counts[value] > 1]


def get_object_containing_key(data, key_name):
    """
    Get all dicts that contain `key_name` within a piece of data
    :param data: the data to search
    :param key_name: the key to find
    :return: list of tuples containing the json path and matched object
    """
    matches = []
    for match in parse(f"$..{key_name}").find(data):
        parent_block = get_parent_block_from_match(match)
        matches.append((str(match.full_path), match.context.value, parent_block))
    return matches


def get_parent_block_from_match(match) -> dict | None:
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
    if (
        str(match.full_path.left).endswith(f".{key}")
        or str(match.full_path.left) == key
    ):
        return match.value
    return get_element_value(key, match.context)


def json_path_position(match) -> tuple[int, ...]:
    """
    Given a match, whose json path will look like 'sections[x].groups[y].blocks[z]...'
    return a tuple of (x, y, z, ...) to represent the position of the match within the schema
    """
    path = str(match.full_path)
    indices = re.findall(r"\[(\d+)]", path)
    return tuple(int(index) for index in indices)


def get_context_from_match(match):
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
    def __init__(self, schema):
        self.schema = schema
        self.matches = [
            *parse("$..blocks[*]").find(self.schema),
            *parse("$..[add_block, edit_block, add_or_edit_block, remove_block]").find(
                self.schema
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
            "CalculatedSummary"
        )
        self.grand_calculated_summary_block_ids = self.get_block_ids_for_block_type(
            "GrandCalculatedSummary"
        )
        self.sections = jp.match("$.sections[*]", self.schema)
        self.sections_by_id = {section["id"]: section for section in self.sections}
        self.section_ids = list(self.sections_by_id.keys())
        self.blocks_by_section_id = {
            section["id"]: [
                block for group in section["groups"] for block in group["blocks"]
            ]
            for section in self.sections
        }

        self.groups = jp.match("$..groups[*]", self.schema)
        self.groups_by_id = {group["id"]: group for group in self.groups}
        self.group_ids = list(self.groups_by_id.keys())

        self.supplementary_lists = jp.match(
            "$..supplementary_data.lists[*]", self.schema
        )
        self.list_collectors = jp.match(
            '$..blocks[?(@.type=="ListCollector")]', self.schema
        )
        self.list_collector_names = [
            list_collector["for_list"] for list_collector in self.list_collectors
        ]
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
        return [block["id"] for block in self.blocks if block["type"] == block_type]

    @cached_property
    def list_names_by_dynamic_answer_id(self) -> dict[str, str]:
        answer_id_to_list: dict[str, str] = {}
        for dynamic_answer in jp.match("$..dynamic_answers[*]", self.schema):
            if dynamic_answer["values"]["source"] == "list":
                list_name = dynamic_answer["values"]["identifier"]
                answer_id_to_list.update(
                    {answer["id"]: list_name for answer in dynamic_answer["answers"]}
                )
        return answer_id_to_list

    @cached_property
    def numeric_answer_ranges(self):
        numeric_answer_ranges = {}

        for answer in jp.match("$..answers[*]", self.schema):
            numeric_answer_ranges[answer["id"]] = self._get_numeric_range_values(
                answer, numeric_answer_ranges
            )

        return numeric_answer_ranges

    @cached_property
    def metadata_ids(self):
        if "metadata" in self.schema:
            return [m["name"] for m in self.schema["metadata"]]
        return []

    @cached_property
    def questions_with_context(self):
        return [
            (match.value, get_context_from_match(match))
            for match in parse("$..question").find(self.schema)
            if isinstance(match.value, dict)
        ]

    @property
    def answers_with_context(self):
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

    @property
    def lists_with_context(self):
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
                    self.block_ids.index(block["id"])
                    < self._lists_with_context[list_id]["block_index"]
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
        for answer in answers:
            answers_dict[answer["id"]] = {"answer": answer, **context}
            for option in answer.get("options", []):
                detail_answer = option.get("detail_answer")
                if detail_answer:
                    answers_dict[detail_answer["id"]] = {
                        "answer": detail_answer,
                        **context,
                    }

    @answers_with_context.setter
    def answers_with_context(self, value):
        self._answers_with_context = value

    @cached_property
    def ids(self):
        """
        question_id & answer_id should be globally unique with some exceptions:
            - within a block, ids can be duplicated across variants, but must still be unique outside of the block.
            - answer_ids must be duplicated across add / edit blocks on list collectors which populate the same list.
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
                    # Since unique_ids_per_block is a set, duplicate ids will only be recorded once within the block.
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
        """
        These values will be returned with the json path to them through the object e.g.
            - 'sections.[0].groups[0].blocks[1].question_variants[0].question.question-2'

        Returns: generator yielding (path, value) tuples
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
                    any(
                        ignored_sub_path in full_path
                        for ignored_sub_path in ignored_sub_paths
                    )
                    and str(match.context.context.full_path.right) == "answers"
                )
            if (
                not any(ignored_path in full_path for ignored_path in ignored)
                and not is_list_collector_answer_id
            ):
                yield str(match.full_path.left), match.value

    @cached_property
    def answer_id_to_option_values_map(self):
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
        for question, _ in self.questions_with_context:
            yield from self.get_answers_from_question(question)

    @lru_cache
    def get_answer(self, answer_id):
        return self.answers_with_context[answer_id]["answer"]

    @lru_cache
    def get_answer_type(self, answer_id):
        answer = self.get_answer(answer_id)
        return AnswerType(answer["type"])

    @lru_cache
    def get_group(self, group_id):
        return self.groups_by_id[group_id]

    @lru_cache
    def get_section(self, section_id):
        return self.sections_by_id[section_id]

    @lru_cache
    def get_block(self, block_id):
        return self.blocks_by_id.get(block_id, None)

    @lru_cache
    def get_blocks(self, **filters):
        conditions = []
        for key, value in filters.items():
            conditions.append(f'@.{key}=="{value}"')

        if conditions:
            final_condition = " & ".join(conditions)
            return jp.match(f"$..blocks[?({final_condition})]", self.schema)
        return self.blocks

    @lru_cache
    def get_other_blocks(self, block_id_to_filter, **filters):
        conditions = []
        for key, value in filters.items():
            conditions.append(f'@.{key}=="{value}"')

        if conditions:
            final_condition = " & ".join(conditions)
            return jp.match(
                f'$..blocks[?(@.id!="{block_id_to_filter}" & {final_condition})]',
                self.schema,
            )
        return self.blocks

    @lru_cache
    def has_single_driving_question(self, list_name):
        return (
            len(
                self.get_blocks(type="ListCollectorDrivingQuestion", for_list=list_name)
            )
            == 1
        )

    @staticmethod
    def get_all_questions_for_block(block):
        """Get all questions on a block including variants"""
        questions = []

        for variant in block.get("question_variants", []):
            questions.append(variant["question"])

        single_question = block.get("question")
        if single_question:
            questions.append(single_question)

        return questions

    @lru_cache
    def get_list_collector_answer_ids(self, block_id):
        block = self.blocks_by_id[block_id]
        if "add_or_edit_block" in block:
            return self.get_all_answer_ids(block["add_or_edit_block"]["id"])

        add_answer_ids = self.get_all_answer_ids(block["add_block"]["id"])

        edit_answer_ids = self.get_all_answer_ids(block["edit_block"]["id"])
        return add_answer_ids | edit_answer_ids

    @lru_cache
    def get_list_collector_answer_ids_by_child_block(self, block_id: str):
        block = self.blocks_by_id[block_id]
        return {
            child_block: self.get_all_answer_ids(block[child_block]["id"])
            for child_block in ["add_block", "edit_block", "remove_block"]
        }

    @lru_cache
    def get_all_answer_ids(self, block_id):
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return {
            answer["id"]
            for question in questions
            for answer in self.get_answers_from_question(question)
        }

    @lru_cache
    def get_all_dynamic_answer_ids(self, block_id):
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return {
            answer["id"]
            for question in questions
            for answer in question.get("dynamic_answers", {}).get("answers", [])
        }

    def get_list_name_for_answer_id(self, answer_id: str) -> str | None:
        """
        If the answer is dynamic or in a repeating block or section, return the name of the list it repeats over
        otherwise None
        """
        if list_name := self.list_names_by_dynamic_answer_id.get(answer_id):
            return list_name
        block = self.get_block_by_answer_id(answer_id)
        if list_name := self.list_names_by_repeating_block_id.get(block["id"]):
            return list_name
        if block["type"] == "ListCollector":
            return block["for_list"]
        section = self.get_parent_section_for_block(block["id"])
        if section.get("repeat"):
            return section["repeat"]["for_list"]

    @lru_cache
    def get_first_answer_in_block(self, block_id):
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return self.get_answers_from_question(questions[0])[0]

    @lru_cache
    def _get_path_id(self, path):
        return jp.match1(path + ".id", self.schema)

    @lru_cache
    def get_block_id_by_answer_id(self, answer_id):
        for question, context in self.questions_with_context:
            if block_id := self.get_block_id_for_answer(
                answer_id=answer_id,
                answers=self.get_answers_from_question(question),
                context=context,
            ):
                return block_id

    @staticmethod
    def get_block_id_for_answer(*, answer_id, answers, context):
        for answer in answers:
            if answer_id == answer["id"]:
                return context["block"]
            for option in answer.get("options", []):
                detail_answer = option.get("detail_answer")
                if detail_answer and answer_id == detail_answer["id"]:
                    return context["block"]

    @lru_cache
    def get_block_by_answer_id(self, answer_id):
        block_id = self.get_block_id_by_answer_id(answer_id)

        return self.get_block(block_id)

    def _get_numeric_range_values(self, answer, answer_ranges):
        min_value = answer.get("minimum", {}).get("value", {})
        max_value = answer.get("maximum", {}).get("value", {})
        min_referred = (
            min_value.get("identifier") if isinstance(min_value, dict) else None
        )
        max_referred = (
            max_value.get("identifier") if isinstance(max_value, dict) else None
        )

        exclusive = answer.get("exclusive", False)
        decimal_places = answer.get("decimal_places", 0)

        return {
            "min": self._get_answer_minimum(
                min_value, decimal_places, exclusive, answer_ranges
            ),
            "max": self._get_answer_maximum(
                max_value, decimal_places, exclusive, answer_ranges
            ),
            "decimal_places": decimal_places,
            "min_referred": min_referred,
            "max_referred": max_referred,
            "default": answer.get("default"),
        }

    def _get_answer_minimum(
        self, defined_minimum, decimal_places, exclusive, answer_ranges
    ):
        minimum_value = self._get_numeric_value(defined_minimum, 0, answer_ranges)
        if exclusive:
            return minimum_value + (1 / 10**decimal_places)
        return minimum_value

    def _get_answer_maximum(
        self, defined_maximum, decimal_places, exclusive, answer_ranges
    ):
        maximum_value = self._get_numeric_value(
            defined_maximum, MAX_NUMBER, answer_ranges
        )
        if exclusive:
            return maximum_value - (1 / 10**decimal_places)
        return maximum_value

    def _get_numeric_value(self, defined_value, system_default, answer_ranges):
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
        """
        Returns the list of block ids of type source_type used in a calculation object,
        e.g. answers for a calculated summary, or calculated summaries for a grand calculated summary
        """
        if block["calculation"].get("answers_to_calculate"):
            return block["calculation"]["answers_to_calculate"]

        value_sources = get_object_containing_key(
            block["calculation"]["operation"], "source"
        )

        return [
            source[1]["identifier"]
            for source in value_sources
            if source[1]["source"] == source_type
        ]

    def get_answer_ids_for_value_source(
        self, value_source: Mapping[str, str]
    ) -> list[str]:
        """
        Gets the list of answer_ids relating to the provided value source. Either the identifier if its an answer source
        or the list of included answer ids in the case of a calculated or grand calculated summary
        """
        source = value_source["source"]
        identifier = value_source["identifier"]

        if source == "calculated_summary":
            return self.get_calculation_block_ids(
                block=self.get_block(identifier), source_type="answers"
            )
        if source == "grand_calculated_summary":
            return [
                answer_id
                for calculated_summary_id in self.get_calculation_block_ids(
                    block=self.get_block(identifier), source_type="calculated_summary"
                )
                for answer_id in self.get_calculation_block_ids(
                    block=self.get_block(calculated_summary_id), source_type="answers"
                )
            ]
        return [identifier]

    def is_repeating_section(self, section_id: str) -> bool:
        return "repeat" in self.sections_by_id[section_id]

    def get_parent_section_for_block(self, block_id) -> dict | None:
        for section_id, blocks in self.blocks_by_section_id.items():
            for block in blocks:
                if block_id == block["id"]:
                    return self.sections_by_id[section_id]

    def get_parent_list_collector_for_add_block(self, block_id) -> dict | None:
        for blocks in self.blocks_by_section_id.values():
            for block in blocks:
                if (
                    block["type"] == "ListCollector"
                    and block["add_block"]["id"] == block_id
                ):
                    return block["id"]

    def get_parent_list_collector_for_repeating_block(self, block_id) -> dict | None:
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
        parent_section = self.get_parent_section_for_block(block_id)
        return parent_section and self.is_repeating_section(parent_section["id"])

    def get_numeric_value_for_value_source(
        self, *, value_source: Mapping[str, str], answer_ranges: Mapping[str, Mapping]
    ) -> Mapping | None:
        referred_answer = None
        answers_to_calculate = self.get_answer_ids_for_value_source(value_source)
        for answer_id in answers_to_calculate:
            referred_answer = answer_ranges.get(answer_id)
            if referred_answer is None:
                return None
        return referred_answer

    @staticmethod
    def get_answers_from_question(question):
        return [
            *question.get("dynamic_answers", {}).get("answers", []),
            *question.get("answers", []),
        ]

    def get_section_block_ids(self, current_section=None):
        return [block["id"] for block in self.blocks_by_section_id[current_section]]

    def get_section_id_for_block(self, block: Mapping) -> str | None:
        for section_id, blocks in self.blocks_by_section_id.items():
            if block in blocks:
                return section_id

    def get_section_id_for_block_id(self, block_id: str) -> str | None:
        if block := self.get_block(block_id):
            return self.get_section_id_for_block(block)

    def get_section_index_for_section_id(self, section_id: str) -> int:
        for index, section in enumerate(self.sections):
            if section["id"] == section_id:
                return index
