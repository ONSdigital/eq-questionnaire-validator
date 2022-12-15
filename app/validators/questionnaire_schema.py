# pylint: disable=too-many-public-methods
import collections
from collections import defaultdict
from functools import cached_property, lru_cache

import jsonpath_rw_ext as jp
from jsonpath_rw import parse

from app.answer_type import AnswerType

MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


def has_default_route(routing_rules):
    for rule in routing_rules:
        if "goto" not in rule or "when" not in rule["goto"].keys():
            return True
    return False


def get_routing_when_list(routing_rules):
    when_list = []
    for rule in routing_rules:
        when_clause = rule.get("goto", {})
        when_list.append(when_clause)
    return when_list


def is_contained_in_dict_list(dict_list, key_id):
    for dict_to_check in dict_list:
        if dict_to_check["id"] == key_id:
            return True
    return False


def find_duplicates(values):
    return [item for item, count in collections.Counter(values).items() if count > 1]


def get_object_containing_key(data, key_name):
    """
    Get all dicts that contain `key_name` within a piece of data
    :param data: the data to search
    :param key_name: the key to find
    :return: list of tuples containing the json path and matched object
    """
    matches = []
    for match in parse(f"$..{key_name}").find(data):
        matches.append((str(match.full_path), match.context.value))
    return matches


def get_element_value(key, match):
    if (
        str(match.full_path.left).endswith(f".{key}")
        or str(match.full_path.left) == key
    ):
        return match.value
    return get_element_value(key, match.context)


def get_context_from_match(match):
    full_path = str(match.full_path)
    section = get_element_value("sections", match)
    block = get_element_value("blocks", match)
    block_id = block["id"]
    group = get_element_value("groups", match)

    for sub_block in ["add_block", "edit_block", "add_or_edit_block", "remove_block"]:
        if sub_block in full_path and sub_block in block:
            block_id = block[sub_block]["id"]

    return {"section": section["id"], "block": block_id, "group_id": group["id"]}


class QuestionnaireSchema:
    def __init__(self, schema):
        self.schema = schema

        self.blocks = jp.match("$..blocks[*]", self.schema)
        self.sub_blocks = jp.match(
            "$..[add_block, edit_block, add_or_edit_block, remove_block]", self.schema
        )
        self.blocks_by_id = {
            block["id"]: block for block in self.blocks + self.sub_blocks
        }
        self.block_ids = list(self.blocks_by_id.keys())
        self.calculated_summary_block_ids = {
            block["id"]
            for block in self.blocks_by_id.values()
            if block["type"] == "CalculatedSummary"
        }
        self.sections = jp.match("$.sections[*]", self.schema)
        self.sections_by_id = {section["id"]: section for section in self.sections}
        self.section_ids = list(self.sections_by_id.keys())

        self.groups = jp.match("$..groups[*]", self.schema)
        self.groups_by_id = {group["id"]: group for group in self.groups}
        self.group_ids = list(self.groups_by_id.keys())

        self.list_names = jp.match(
            '$..blocks[?(@.type=="ListCollector")].for_list', self.schema
        )

        self._answers_with_context = {}

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

        answers = {}
        for question, context in self.questions_with_context:
            for answer in question.get("answers", []):
                answers[answer["id"]] = {"answer": answer, **context}
                for option in answer.get("options", []):
                    detail_answer = option.get("detail_answer")
                    if detail_answer:
                        answers[detail_answer["id"]] = {
                            "answer": detail_answer,
                            **context,
                        }

        self._answers_with_context = answers
        return self._answers_with_context

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
            for answer in question["answers"]:
                yield answer

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
    def get_all_answer_ids(self, block_id):
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return {
            answer["id"] for question in questions for answer in question["answers"]
        }

    @lru_cache
    def get_first_answer_in_block(self, block_id):
        questions = self.get_all_questions_for_block(self.blocks_by_id[block_id])
        return questions[0]["answers"][0]

    @lru_cache
    def _get_path_id(self, path):
        return jp.match1(path + ".id", self.schema)

    @lru_cache
    def get_block_id_by_answer_id(self, answer_id):
        for question, context in self.questions_with_context:
            for answer in question.get("answers", []):
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

    def _get_numeric_value_for_value_source(
        self, value_source, defined_value, answer_ranges
    ):
        referred_answer = None
        if value_source == "answers":
            referred_answer = answer_ranges.get(defined_value["identifier"])
        elif value_source == "calculated_summary":
            calculated_summary_block = self.get_block(defined_value["identifier"])
            answers_to_calculate = self.get_calculated_answer_ids(
                calculated_summary_block
            )

            for answer_id in answers_to_calculate:
                referred_answer = answer_ranges.get(answer_id)
                if referred_answer is None:
                    return None
        return referred_answer

    def _get_numeric_value(self, defined_value, system_default, answer_ranges):
        if not isinstance(defined_value, dict):
            return defined_value
        if source := defined_value.get("source"):
            referred_answer = self._get_numeric_value_for_value_source(
                value_source=source,
                defined_value=defined_value,
                answer_ranges=answer_ranges,
            )
            # Referred answer is not valid (picked up by _validate_referred_numeric_answer)
            if not referred_answer:
                return None
        return system_default

    @staticmethod
    def get_calculated_answer_ids(block):
        if block["calculation"].get("answers_to_calculate"):
            return block["calculation"]["answers_to_calculate"]

        value_sources = get_object_containing_key(
            block["calculation"]["operation"], "source"
        )

        return [
            source[1]["identifier"]
            for source in value_sources
            if source[1]["source"] == "answers"
        ]
