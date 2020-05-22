import collections
from collections import defaultdict
from functools import cached_property, lru_cache
import jsonpath_rw_ext as jp
from jsonpath_rw import parse


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


@lru_cache
def get_key_index_from_path(key, path):
    position = path.find(key) + len(key + ".[")
    return int(path[position : position + 1])


@lru_cache
def get_element_path(key, path):
    position = path.find(key)
    return path[: position + len(key + ".[0]")]


# pylint: disable=too-many-public-methods
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
        self.sections = jp.match("$.sections[*]", self.schema)
        self.sections_by_id = {section["id"]: section for section in self.sections}
        self.section_ids = list(self.sections_by_id.keys())

        self.groups = jp.match("$..groups[*]", self.schema)
        self.groups_by_id = {group["id"]: group for group in self.groups}
        self.group_ids = list(self.groups_by_id.keys())

        self.list_names = jp.match(
            '$..blocks[?(@.type=="ListCollector")].for_list', self.schema
        )

    @cached_property
    def metadata_ids(self):
        if "metadata" in self.schema:
            return [m["name"] for m in self.schema["metadata"]]
        return []

    @cached_property
    def questions_with_context(self):
        for match in parse("$..question").find(self.schema):
            yield match.value, self.get_context_from_path(str(match.full_path))

    @cached_property
    def answers_with_context(self):
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

        return answers

    @cached_property
    def is_hub_enabled(self):
        return self.schema.get("hub", {}).get("enabled")

    @cached_property
    def ids(self):
        """
        question_id & answer_id should be globally unique with some exceptions:
            - within a block, ids can be duplicated across variants, but must still be unique outside of the block.
            - answer_ids must be duplicated across add / edit blocks on list collectors which populate the same list.
        """
        unique_ids_per_block = defaultdict(set)
        non_block_ids = []
        all_ids = []

        for path, value in self.id_paths:
            if "blocks" in path:
                # Generate a string path and add it to the set representing the ids in that path
                path_list = path.split(".")

                block_path = path_list[: path_list.index("blocks") + 2]

                string_path = ".".join(block_path)
                # Since unique_ids_per_block is a set, duplicate ids will only be recorded once within the block.
                unique_ids_per_block[string_path].add(value)
            else:
                non_block_ids.append(value)

        for block_ids in unique_ids_per_block.values():
            all_ids.extend(block_ids)
        all_ids.extend(non_block_ids)

        return all_ids

    @cached_property
    def id_paths(self):
        """
        These values will be returned with the json path to them through the object e.g.
            - 'sections.[0].groups[0].blocks[1].question_variants[0].question.question-2'

        Returns: generator yielding (path, value) tuples
        """
        ignored_paths = [
            "routing_rules",
            "skip_conditions",
            "when",
            "edit_block.question.answers",
            "add_block.question.answers",
            "remove_block.question.answers",
            "edit_block.question_variants.answers",
            "add_block.question_variants.answers",
            "remove_block.question_variants.answers",
        ]

        for match in parse("$..id").find(self.schema):
            full_path = str(match.full_path)
            if not any(ignored_path in full_path for ignored_path in ignored_paths):
                yield str(match.full_path)[:-3], match.value

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
    def get_group(self, group_id):
        return self.groups_by_id[group_id]

    @lru_cache
    def get_section(self, section_id):
        return self.sections_by_id[section_id]

    @lru_cache
    def get_block(self, block_id):
        return self.blocks_by_id[block_id]

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
    def get_block_key_context(self, block_id, key_name):
        """
        Get all dicts that contain `key_name` within a block
        :param block_id: the id of the block to search
        :param key_name: the key to find
        :return: list of dicts containing the key name, otherwise returns None
        """
        matches = []
        for match in parse(f"$..{key_name}").find(self.blocks_by_id[block_id]):
            matches.append(match.context.value)
        return matches

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
        """ Get all questions on a block including variants"""
        questions = []

        for variant in block.get("question_variants", []):
            questions.append(variant["question"])

        single_question = block.get("question")
        if single_question:
            questions.append(single_question)

        return questions

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
    def get_context_from_path(self, full_path):
        section_index = get_key_index_from_path("sections", full_path)

        block_path = get_element_path("blocks", full_path)
        group_path = get_element_path("groups", full_path)

        group_id = self._get_path_id(group_path)
        block_id = self._get_path_id(block_path)

        if any(
            sub_block in full_path
            for sub_block in [
                "add_block",
                "edit_block",
                "add_or_edit_block",
                "remove_block",
            ]
        ):
            key_path = full_path[len(block_path) + 1 :]
            key = key_path[: key_path.find(".question")]
            block_id = self.blocks_by_id[block_id][key]["id"]

        return {
            "section": self.section_ids[section_index],
            "block": block_id,
            "group_id": group_id,
        }
