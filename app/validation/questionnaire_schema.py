from collections import defaultdict
from functools import cached_property, lru_cache


class QuestionnaireSchema:
    def __init__(self, schema):
        self.schema = schema

    def has_single_list_collector(self, list_name, section):
        return (
            len(
                [
                    True
                    for block in self.get_blocks_for_section(section)
                    if block["type"] == "ListCollector"
                    and list_name == block["for_list"]
                ]
            )
            == 1
        )

    @lru_cache
    def has_single_driving_question(self, list_name):
        return len(self.get_driving_questions(list_name)) == 1

    @lru_cache
    def get_driving_questions(self, list_name):
        driving_blocks = []

        for section in self.schema.get("sections"):
            driving_blocks.extend(
                [
                    block
                    for block in self.get_blocks_for_section(section)
                    if block["type"] == "ListCollectorDrivingQuestion"
                    and block["for_list"] == list_name
                ]
            )

        return driving_blocks

    @staticmethod
    def get_blocks_for_section(section):
        return [block for group in section["groups"] for block in group["blocks"]]

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

    @classmethod
    def _get_sub_block_context(cls, section, group, block):
        for sub_block_type in (
            "add_block",
            "edit_block",
            "remove_block",
            "add_or_edit_block",
        ):
            sub_block = block.get(sub_block_type)
            if sub_block:
                for question in cls.get_all_questions_for_block(sub_block):
                    context = {
                        "block": sub_block["id"],
                        "group_id": group["id"],
                        "section": section["id"],
                    }
                    yield question, context

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

    @cached_property
    def questions_with_context(self):
        for section in self.schema.get("sections"):
            for group in section.get("groups"):
                for block in group.get("blocks"):
                    for question in self.get_all_questions_for_block(block):
                        context = {
                            "block": block["id"],
                            "group_id": group["id"],
                            "section": section["id"],
                        }
                        yield question, context

                        for sub_block, context in self._get_sub_block_context(
                            section, group, block
                        ):
                            yield sub_block, context

    @cached_property
    def list_names(self):
        list_names = []
        for section in self.schema["sections"]:
            for block in self.get_blocks_for_section(section):
                if block["type"] == "ListCollector":
                    list_names.append(block["for_list"])
        return list_names

    @cached_property
    def block_ids(self):
        block_ids = []
        for section in self.schema["sections"]:
            for block in self.get_blocks_for_section(section):
                block_ids.append(block["id"])
                for sub_block in {
                    "add_block",
                    "edit_block",
                    "remove_block",
                    "add_or_edit_block",
                }:
                    if sub_block in block:
                        block_ids.append(block[sub_block]["id"])

        return block_ids

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
