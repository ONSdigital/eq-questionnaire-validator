from collections import defaultdict

from app import error_messages
from app.validators.answers import get_answer_validator
from app.validators.blocks import get_block_validator
from app.validators.questionnaire_schema import get_object_containing_key
from app.validators.questions import get_question_validator
from app.validators.routing.new_routing_validator import NewRoutingValidator
from app.validators.routing.routing_validator import RoutingValidator
from app.validators.routing.when_rule_validator import WhenRuleValidator
from app.validators.rules.rule_validator import RulesValidator
from app.validators.validator import Validator
from app.validators.value_source_validator import ValueSourceValidator


class SectionValidator(Validator):
    def __init__(self, schema_element, questionnaire_schema):
        super().__init__(schema_element)
        self.section = schema_element
        self.questionnaire_schema = questionnaire_schema
        self.context["section_id"] = self.section["id"]

    def validate(self):
        self.validate_repeat()
        self.validate_summary()
        self.validate_value_sources()
        if self.errors:  # return when value sources are not valid
            return self.errors
        self.validate_groups()
        self.validate_section_enabled()
        self.validate_number_of_list_collectors()
        self.validate_section_summary_items()
        return self.errors

    def validate_repeat(self):
        section_repeat = self.section.get("repeat", None)

        if section_repeat:
            self.validate_list_exists(section_repeat["for_list"])

    def validate_summary(self):
        section_summary = self.section.get("summary", None)

        if section_summary:
            for item in section_summary.get("items", []):
                self.validate_list_exists(item.get("for_list"))

    def validate_section_enabled(self):
        section_enabled = self.section.get("enabled", None)

        if isinstance(section_enabled, list):
            for enabled in section_enabled:
                when = enabled["when"]
                when_validator = WhenRuleValidator(
                    when, self.section["id"], self.questionnaire_schema
                )
                self.errors += when_validator.validate()

        elif isinstance(section_enabled, dict):
            when = section_enabled["when"]
            when_validator = RulesValidator(
                when, self.section["id"], self.questionnaire_schema
            )
            self.errors += when_validator.validate()

    def validate_list_exists(self, list_name):
        if list_name not in self.questionnaire_schema.list_names:
            self.add_error(error_messages.FOR_LIST_NEVER_POPULATED, list_name=list_name)

    def validate_skip_conditions(self, skip_conditions, origin_id):
        for skip_condition in skip_conditions:
            when_validator = WhenRuleValidator(
                skip_condition["when"], origin_id, self.questionnaire_schema
            )
            self.errors += when_validator.validate()

    def validate_new_skip_conditions(self, skip_condition, origin_id):
        when_validator = RulesValidator(
            skip_condition["when"], origin_id, self.questionnaire_schema
        )
        self.errors += when_validator.validate()

    def validate_value_sources(self):
        source_references = get_object_containing_key(self.section, "identifier")
        for json_path, source_reference in source_references:
            if "source" in source_reference:
                value_source_validator = ValueSourceValidator(
                    value_source=source_reference,
                    json_path=json_path,
                    questionnaire_schema=self.questionnaire_schema,
                )
                self.errors += value_source_validator.validate()

    def validate_groups(self):
        for group in self.section["groups"]:
            self.validate_routing(group, group)
            self.validate_blocks(group["id"])

    def validate_blocks(self, group_id):
        group = self.questionnaire_schema.get_group(group_id)

        for block in group.get("blocks"):
            self.validate_routing(block, group)

            block_validator = get_block_validator(block, self.questionnaire_schema)
            self.errors += block_validator.validate()

            self.validate_question(block)
            self.validate_variants(block)

    def validate_routing(self, schema_element, group):
        if "routing_rules" in schema_element:
            if any("goto" in rule for rule in schema_element["routing_rules"]):
                routing_validator = RoutingValidator(
                    schema_element, group, self.questionnaire_schema
                )
            else:
                routing_validator = NewRoutingValidator(
                    routing_rules=schema_element["routing_rules"],
                    group=group,
                    origin_id=schema_element["id"],
                    questionnaire_schema=self.questionnaire_schema,
                )
            self.errors += routing_validator.validate()
        if "skip_conditions" in schema_element:
            if isinstance(schema_element["skip_conditions"], list):
                self.validate_skip_conditions(
                    schema_element["skip_conditions"], schema_element["id"]
                )
            elif isinstance(schema_element["skip_conditions"], dict):
                self.validate_new_skip_conditions(
                    schema_element["skip_conditions"], schema_element["id"]
                )

    def validate_question(self, block_or_variant):
        question = block_or_variant.get("question")

        if question:
            question_validator = get_question_validator(
                question, self.questionnaire_schema
            )

            self.errors += question_validator.validate()

            for answer in question.get("answers", []):
                answer_validator = get_answer_validator(
                    answer, self.questionnaire_schema
                )

                answer_validator.validate()

                if question.get("summary") and answer["type"] not in [
                    "TextField",
                    "Checkbox",
                    "Number",
                ]:
                    self.add_error(
                        error_messages.UNSUPPORTED_QUESTION_SUMMARY_ANSWER_TYPE,
                        answer_id=answer["id"],
                    )
                self.errors += answer_validator.errors

    def validate_variants(self, block):
        question_variants = block.get("question_variants", [])
        content_variants = block.get("content_variants", [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            self.validate_question(variant)

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            self.add_error(
                error_messages.VARIANTS_HAS_ONE_VARIANT, block_id=block["id"]
            )

        for variant in all_variants:
            when_clause = variant.get("when", [])

            if isinstance(when_clause, list):
                when_validator = WhenRuleValidator(
                    when_clause, block["id"], self.questionnaire_schema
                )
                self.errors += when_validator.validate()

            elif isinstance(when_clause, dict):
                when_validator = RulesValidator(
                    when_clause, self.section["id"], self.questionnaire_schema
                )
                self.errors += when_validator.validate()

        self.validate_variant_fields(block, question_variants)

    def validate_variant_fields(self, block, variants):
        """Ensure consistency between relevant fields in variants

        - Ensure that question_ids are the same across all variants.
        - Ensure answer_ids are the same across all variants.
        - Ensure question types are the same across all variants.
        - Ensure answer types are the same across all variants.
        - Ensure default answers are the same across all variants.
        """
        if not variants:
            return

        results = self._get_question_variant_fields_sets(variants)

        if len(results["number_of_answers"]) > 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_DIFFERENT_ANSWER_LIST_LENGTHS,
                block_id=block["id"],
            )

        if len(results["question_ids"]) != 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_DIFFERENT_QUESTION_IDS,
                block_id=block["id"],
                question_ids=results["question_ids"],
            )

        if len(results["question_types"]) != 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_MULTIPLE_QUESTION_TYPES,
                block_id=block["id"],
                question_types=results["question_types"],
            )

        if len(results["default_answers"]) > 1:
            self.add_error(
                error_messages.VARIANTS_HAVE_DIFFERENT_DEFAULT_ANSWERS,
                block_id=block["id"],
                question_ids=results["question_ids"],
            )

        if len(results["answer_ids"]) != next(iter(results["number_of_answers"])):
            self.add_error(
                error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_IDS,
                block_id=block["id"],
                answer_ids=results["answer_ids"],
            )

        for answer_id, type_set in results["answer_types"].items():
            if len(type_set) != 1:
                self.add_error(
                    error_messages.VARIANTS_HAVE_MISMATCHED_ANSWER_TYPES,
                    block_id=block["id"],
                    answer_types=type_set,
                    answer_id=answer_id,
                )

    @staticmethod
    def _get_question_variant_fields_sets(variants):
        results = {
            "question_ids": set(),
            "question_types": set(),
            "answer_ids": set(),
            "answer_types": defaultdict(set),
            "default_answers": set(),
            "number_of_answers": set(),
        }

        for variant in variants:
            question_variant = variant["question"]
            results["question_ids"].add(question_variant["id"])
            results["question_types"].add(question_variant["type"])

            for answer in question_variant["answers"]:
                results["answer_ids"].add(answer["id"])
                results["answer_types"][answer["id"]].add(answer["type"])
                results["default_answers"].add(answer.get("default"))

            results["number_of_answers"].add(len(results["answer_ids"]))

        # Code to handle comparison of variants which contain a MutuallyExclusive answer type
        if (
            len(results["question_types"]) > 1
            and "MutuallyExclusive" in results["question_types"]
        ):
            results["question_types"].remove("MutuallyExclusive")

            results["answer_ids"].clear()

            results["number_of_answers"].clear()

            for variant in variants:
                if variant["question"]["type"] == "MutuallyExclusive":
                    non_exclusive_answer = variant["question"]["answers"][0]
                    results["answer_ids"].add(non_exclusive_answer["id"])
                else:
                    for answer in variant["question"]["answers"]:
                        results["answer_ids"].add(answer["id"])

                results["number_of_answers"].add(len(results["answer_ids"]))

        return results

    def validate_number_of_list_collectors(self):
        if (
            self.has_list_summary_with_non_item_answers()
            and self.has_multiple_list_collectors()
        ):
            self.add_error(error_messages.MULTIPLE_LIST_COLLECTORS)

    def has_list_summary_with_non_item_answers(self):
        if summary := self.schema_element.get("summary"):
            show_non_item_answers = summary.get("show_non_item_answers")
            return summary.get("items") and show_non_item_answers

    def has_multiple_list_collectors(self):
        list_collectors = []
        for group in self.schema_element.get("groups"):
            list_collectors.extend(
                block
                for block in group.get("blocks")
                if block["type"] in ["ListCollector"]
            )

        return len(list_collectors) > 1

    def validate_section_summary_items(self):
        summary_items = self.schema_element.get("summary", {}).get("items", [])
        if not summary_items:
            return None

        blocks = self.questionnaire_schema.get_blocks(type="ListCollector")
        list_collector_answer_ids_by_list = defaultdict(list)
        for block in blocks:
            list_collector_answer_ids_by_list[block["for_list"]].extend(
                self.questionnaire_schema.get_list_collector_answer_ids(block["id"])
            )

        for item in summary_items:
            list_collector_answer_ids_for_list = list_collector_answer_ids_by_list[
                item["for_list"]
            ]

            if item_anchor_answer_id := item.get("item_anchor_answer_id"):
                self._validate_item_anchor_answer_id_belongs_to_list_collector(
                    item_anchor_answer_id,
                    list_collector_answer_ids_for_list,
                    item["for_list"],
                )

            for answer_source in item.get("related_answers", []):
                self._validate_related_answer_belong_to_list_collector(
                    answer_source, list_collector_answer_ids_for_list
                )
                self._validate_related_answer_has_label(answer_source)

    def _validate_related_answer_belong_to_list_collector(
        self, answer_source, list_collector_answer_ids
    ):
        if answer_source["identifier"] not in list_collector_answer_ids:
            self.add_error(
                error_messages.RELATED_ANSWERS_NOT_IN_LIST_COLLECTOR,
                id=answer_source["identifier"],
            )

    def _validate_item_anchor_answer_id_belongs_to_list_collector(
        self, anchor_answer_id, list_collector_answer_ids, list_name
    ):
        if anchor_answer_id not in list_collector_answer_ids:
            self.add_error(
                error_messages.ITEM_ANCHOR_ANSWER_ID_NOT_IN_LIST_COLLECTOR.format(
                    answer_id=anchor_answer_id, list_name=list_name
                ),
                id=anchor_answer_id,
            )

    def _validate_related_answer_has_label(self, answer_source):
        answer = self.questionnaire_schema.get_answer(answer_source["identifier"])
        if not answer.get("label"):
            self.add_error(
                error_messages.NO_LABEL_FOR_RELATED_ANSWER.format(
                    answer_id=answer_source["identifier"],
                ),
                id=answer_source["identifier"],
            )
