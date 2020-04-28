from collections import defaultdict
from functools import cached_property, lru_cache
import jsonpath_rw_ext as jp
from jsonpath_rw import parse


class QuestionnaireSchema:
    def __init__(self, schema):
        self.schema = schema

        self.blocks = jp.match("$..blocks[*]", self.schema)
        self.blocks_by_id = {block["id"]: block for block in self.blocks}
        self.section_ids = jp.match("$.sections[*].id", self.schema)
        self.group_ids = jp.match("$..groups[*].id", self.schema)
        self.block_ids = [block["id"] for block in self.blocks]

        self.sub_block_ids = jp.match(
            "$..[add_block, edit_block, add_or_edit_block, remove_block].id",
            self.schema,
        )
        self.list_names = jp.match(
            '$..blocks[?(@.type=="ListCollector")].for_list', self.schema
        )

    @lru_cache
    def has_single_list_collector(self, list_name, section_id):
        return (
            len(
                jp.match(
                    f'$..sections[?(@.id=={section_id})]..blocks[?(@.type=="ListCollector" & @.for_list=="{list_name}")]',
                    self.schema,
                )
            )
            == 1
        )

    @lru_cache
    def get_driving_question_blocks(self, list_name):
        return jp.match(
            f'$..blocks[?(@.type=="ListCollectorDrivingQuestion" & @.for_list=="{list_name}")]',
            self.schema,
        )

    @lru_cache
    def has_single_driving_question(self, list_name):
        return len(self.get_driving_question_blocks(list_name)) == 1

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

    @staticmethod
    def get_key_index_from_path(key, path):
        position = path.find(key) + len(key + ".[")
        return int(path[position : position + 1])

    @staticmethod
    def get_element_path(key, path):
        position = path.find(key)
        return path[: position + len(key + ".[0]")]

    @lru_cache
    def get_context_from_path(self, full_path):
        section_index = self.get_key_index_from_path("sections", full_path)

        block_path = self.get_element_path("blocks", full_path)
        group_path = self.get_element_path("groups", full_path)

        group_id = jp.match1(group_path + ".id", self.schema)
        block_id = jp.match1(block_path + ".id", self.schema)

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

    @cached_property
    def questions_with_context(self):
        return [
            (match.value, self.get_context_from_path(str(match.full_path)))
            for match in parse("$..question").find(self.schema)
        ]

    @cached_property
    def is_hub_enabled(self):
        return self.schema.get("hub", {}).get("enabled")

    def find_key(self, schema_json, key_to_find, path=None):
        """ generate a list of values with a key of `key_to_find`.

        These values will be returned with the json pointer path to them through the object e.g.
            - '/sections/0/groups/0/blocks/1/question_variants/0/question/question-2'

        Returns: generator yielding (path, value) tuples
        """

        if path is None:
            path = ""

        ignored_keys = ["routing_rules", "skip_conditions", "when"]
        ignored_sub_paths = [
            "edit_block/question",
            "add_block/question",
            "remove_block/question",
            "edit_block/question_variants",
            "add_block/question_variants",
            "remove_block/question_variants",
        ]

        for key, value in schema_json.items():
            new_path = f"{path}/{key}"

            if key == key_to_find:
                yield path, value
            elif key in ignored_keys:
                continue
            elif (
                any([ignored_path in new_path for ignored_path in ignored_sub_paths])
                and key == "answers"
            ):
                continue
            elif isinstance(value, dict):
                yield from self.find_key(value, key_to_find, new_path)
            elif isinstance(value, list):
                for index, schema_item in enumerate(value):
                    indexed_path = new_path + f"/{index}"
                    if isinstance(schema_item, dict):
                        yield from self.find_key(schema_item, key_to_find, indexed_path)
