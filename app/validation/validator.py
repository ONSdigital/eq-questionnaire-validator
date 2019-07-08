import os
import pathlib
import re
from collections import defaultdict
from datetime import datetime
from json import load

from dateutil.relativedelta import relativedelta
from jsonschema import SchemaError, RefResolver, validate, ValidationError
from jsonschema.exceptions import best_match

MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


class Validator:  # pylint: disable=too-many-lines
    def __init__(self):
        with open('schemas/questionnaire_v1.json', encoding='utf8') as schema_data:
            self.schema = load(schema_data)

        self._list_collector_answer_ids = {}
        self._list_names = []

    def validate_schema(self, json_to_validate):
        """
        Validates the json schema provided is correct
        :param json_to_validate: json schema to be validated
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        all_errors = {
            'schema_errors': self._validate_json_against_schema(json_to_validate)
        }

        validation_errors = []
        validation_errors.extend(self._validate_schema_contain_metadata(json_to_validate))
        validation_errors.extend(self._validate_duplicates(json_to_validate))

        try:
            all_groups = self._build_groups_list(json_to_validate)
        except self.CoreStructureError as cve:
            validation_errors.extend([{'message': cve.message}])
        else:
            numeric_answer_ranges = {}
            answers_with_parent_ids = self._get_answers_with_parent_ids(json_to_validate)
            self._list_names = self._get_list_names(json_to_validate)

            for section in json_to_validate['sections']:
                for group in section['groups']:

                    validation_errors.extend(self._validate_routing_rules(group, all_groups, answers_with_parent_ids))

                    for skip_condition in group.get('skip_conditions', []):
                        validation_errors.extend(self._validate_skip_condition(skip_condition, answers_with_parent_ids, group))

                    validation_errors.extend(
                        self._validate_blocks(json_to_validate,
                                              section,
                                              group,
                                              all_groups,
                                              answers_with_parent_ids,
                                              numeric_answer_ranges)
                    )

        all_errors['validation_errors'] = validation_errors

        return all_errors

    def _build_groups_list(self, json_to_validate):
        sections = json_to_validate.get('sections', [])
        if not sections:
            raise self.CoreStructureError(
                'Sections key missing from schema or is empty list'
            )

        sections_with_empty_groups = [
            section.get('id', section) for section in sections if not section.get('groups')
        ]
        if sections_with_empty_groups:
            raise self.CoreStructureError(
                f'Section "{sections_with_empty_groups[0]}" is missing groups key or groups list is empty'
            )

        all_groups = [group for section in sections for group in section.get('groups')]
        groups_with_empty_blocks = [
            group.get('id', group)
            for group in all_groups
            if not group.get('blocks')
        ]
        if groups_with_empty_blocks:
            raise self.CoreStructureError(
                f'Group "{groups_with_empty_blocks[0]}" is missing blocks key or blocks list is empty'
            )

        return all_groups

    def _validate_routing_rules(self, group, all_groups, answers_with_parent_ids):
        errors = []

        errors.extend(self._validate_routing_rules_default(group.get('routing_rules', []), group))
        for rule in group.get('routing_rules', []):
            errors.extend(self._validate_schema_routing_rule_routes_to_valid_target(group['blocks'], 'block', rule))
            errors.extend(self._validate_schema_routing_rule_routes_to_valid_target(all_groups, 'group', rule))
            errors.extend(self._validate_routing_rule(rule, answers_with_parent_ids, group))

        return errors

    # pylint: disable=too-complex
    def _validate_blocks(self, json_to_validate, section, group, all_groups, answers_with_parent_ids, numeric_answer_ranges):  # noqa: C901
        errors = []
        for block in group.get('blocks'):
            if section == json_to_validate['sections'][-1] \
                    and group == section['groups'][-1] \
                    and block == group['blocks'][-1]:
                errors.extend(self._validate_schema_contains_submission_page(schema=json_to_validate, last_block=block))

            errors.extend(self._validate_routing_rules_default(block.get('routing_rules', []), block))

            for rule in block.get('routing_rules', []):
                errors.extend(self._validate_schema_routing_rule_routes_to_valid_target(group['blocks'], 'block', rule))
                errors.extend(self._validate_schema_routing_rule_routes_to_valid_target(all_groups, 'group', rule))

                errors.extend(self._validate_routing_rule(rule, answers_with_parent_ids, block))

            for skip_condition in block.get('skip_conditions', []):
                errors.extend(self._validate_skip_condition(skip_condition, answers_with_parent_ids, block))

            if block['type'] == 'CalculatedSummary':
                errors.extend(self._validate_calculated_summary_type(block, answers_with_parent_ids))
            elif block['type'] == 'PrimaryPersonListCollector':
                try:
                    errors.extend(self._validate_primary_person_list_collector(block))
                except KeyError as e:
                    errors.append(f'Missing key in list collector: {e}')
            elif block['type'] == 'ListCollector':
                try:
                    errors.extend(self._validate_list_collector(block))
                except KeyError as e:
                    errors.append(f'Missing key in list collector: {e}')
            elif block['type'] == 'PrimaryPersonListAddOrEditQuestion':
                errors.append(f'Block type: {block["type"]} not allowed outside of '
                              'PrimaryPersonListCollectors')
            elif block['type'] in ['ListAddQuestion', 'ListEditQuestion',
                                   'ListRemoveQuestion']:
                errors.append(f'Block type: {block["type"]} not allowed outside of '
                              'ListCollectors')

            errors.extend(self._validate_questions(block, numeric_answer_ranges))

            valid_metadata_ids = []
            if 'metadata' in json_to_validate:
                valid_metadata_ids = [m['name'] for m in json_to_validate['metadata']]

            errors.extend(self._validate_placeholders(block, answers_with_parent_ids, valid_metadata_ids))

            errors.extend(self._validate_variants(block, answers_with_parent_ids, numeric_answer_ranges))

        return errors

    def _validate_questions(self, block_or_variant, numeric_answer_ranges):
        errors = []

        questions = block_or_variant.get('questions', [])
        question = block_or_variant.get('question')

        if question:
            questions.append(question)

        for question in questions:
            errors.extend(self._validate_calculated_ids_in_answers_to_calculate_exists(question))
            errors.extend(self._validate_date_range(question))
            errors.extend(self._validate_mutually_exclusive(question))

            for answer in question.get('answers', []):
                errors.extend(self._validate_routing_on_answer_options(block_or_variant, answer))
                errors.extend(self._validate_duplicate_options(answer))
                errors.extend(self._validate_totaliser_defines_decimal_places(answer))

                if answer['type'] == 'Date':
                    if 'minimum' in answer and 'maximum' in answer:
                        errors.extend(self._validate_minimum_and_maximum_offset_date(answer))

                if answer['type'] in ['Number', 'Currency', 'Percentage']:
                    numeric_answer_ranges[answer.get('id')] = self._get_numeric_range_values(
                        answer, numeric_answer_ranges)

                    errors.extend(self._validate_numeric_answer_types(answer, numeric_answer_ranges))

        return errors

    def _ensure_relevant_variant_fields_are_consistent(self, block, variants):
        """ Ensure consistency between relevant fields in variants

        - Ensure that question_ids are the same across all variants.
        - Ensure answer_ids are the same across all variants.
        - Ensure question types are the same across all variants.
        - Ensure answer types are the same across all variants.
        """
        if not variants:
            return []

        errors = []

        question_ids = set()
        answer_ids = set()
        question_types = set()

        answer_types = defaultdict(set)

        number_of_answers = set()

        for variant in variants:
            question_variant = variant['question']
            question_ids.add(question_variant['id'])
            question_types.add(question_variant['type'])

            number_of_answers.add(len(variant['question']['answers']))

            if len(number_of_answers) > 1:
                errors.append(self._error_message('Variants in block: {} contain different numbers of answers'.format(block['id'])))

            for answer in question_variant['answers']:
                answer_ids.add(answer['id'])
                answer_types[answer['id']].add(answer['type'])

        if len(question_ids) != 1:
            errors.append(self._error_message(
                'Variants contain more than one question_id for block: {}. Found ids: {}'.format(block['id'], question_ids)))

        if len(question_types) != 1:
            errors.append(self._error_message(
                'Variants have more than one question type for block: {}. Found types: {}'.format(block['id'], question_types)))

        if len(answer_ids) != next(iter(number_of_answers)):
            errors.append(self._error_message(
                'Variants have mismatched answer_ids for block: {}. Found ids: {}.'.format(block['id'], answer_ids)))

        for answer_id, type_set in answer_types.items():
            if len(type_set) != 1:
                errors.append(
                    self._error_message(
                        'Variants have mismatched answer types for block: {}. Found types: {} for answer ID: {}.'.format(
                            block['id'], type_set, answer_id
                        )
                    )
                )
        return errors

    def _validate_variants(self, block, answer_ids_with_group_id, numeric_answer_ranges):
        errors = []

        question_variants = block.get('question_variants', [])
        content_variants = block.get('content_variants', [])

        all_variants = question_variants + content_variants

        for variant in question_variants:
            errors.extend(self._validate_questions(variant, numeric_answer_ranges))

        # This is validated in json schema, but the error message is not good at the moment.
        if len(question_variants) == 1 or len(content_variants) == 1:
            errors.append(self._error_message('Variants contains fewer than two variants - block: {}'.format(block['id'])))

        for variant in all_variants:
            errors.extend(self._validate_when_rule(variant.get('when', []), answer_ids_with_group_id, block['id']))

        errors.extend(self._ensure_relevant_variant_fields_are_consistent(block, question_variants))

        return errors

    def _validate_json_against_schema(self, json_to_validate):
        try:
            base_uri = pathlib.Path(os.path.abspath('schemas/questionnaire_v1.json')).as_uri()
            resolver = RefResolver(base_uri=base_uri, referrer=self.schema)
            validate(json_to_validate, self.schema, resolver=resolver)
            return {}
        except ValidationError as e:
            return {
                'message': e.message,
                'predicted_cause': best_match([e]).message,
                'path': str(e.path),
            }
        except SchemaError as e:
            return '{}'.format(e)

    def _validate_schema_contain_metadata(self, schema):

        errors = []

        # user_id and period_id required downstream for receipting
        # ru_name required for template rendering in default and NI theme
        default_metadata = ['user_id', 'period_id']
        schema_metadata = [metadata_field['name'] for metadata_field in schema['metadata']]

        if len(schema_metadata) != len(set(schema_metadata)):
            errors.append(self._error_message('Mandatory Metadata - contains duplicates'))

        required_metadata_names = ['user_id', 'period_id']
        for metadata_name in required_metadata_names:
            if metadata_name not in schema_metadata:
                errors.append(self._error_message(
                    'Mandatory Metadata - `{}` not specified in metadata field'.format(metadata_name)))

        if schema['theme'] in ['default', 'northernireland']:
            if 'ru_name' not in schema_metadata:
                errors.append(self._error_message('Metadata - ru_name not specified in metadata field'))
            default_metadata.append('ru_name')

        # Find all words that precede any of:
        all_metadata = set(re.findall(r"((?<!collection_metadata\[\')(?<=metadata\[\')\w+"  # metadata[' not _metadata['
                                      r'|(?<!collection_metadata\.)(?<=metadata\.)\w+'  # metadata. not _metadata.
                                      r"|(?<=meta\': \')\w+)", str(schema)))  # meta': '

        # Checks if piped/routed metadata is defined in the schema
        for metadata in all_metadata:
            if metadata not in schema_metadata:
                errors.append(self._error_message('Metadata - {} not specified in metadata field'.format(metadata)))

        return errors

    def _validate_calculated_ids_in_answers_to_calculate_exists(self, question):
        """
        Validates that any answer ids within the 'answer_to_group'
        list are existing answers within the question
        """

        errors = []

        if question['type'] == 'Calculated':
            answer_ids = [answer['id'] for answer in question.get('answers')]
            for calculation in question.get('calculations'):
                for answer_id in calculation['answers_to_calculate']:
                    if answer_id not in answer_ids:
                        invalid_answer_id_error = 'Answer id - {} does not exist within this question - {}' \
                            .format(answer_id, question['id'])
                        errors.append(self._error_message(invalid_answer_id_error))

        return errors

    def _validate_schema_routing_rule_routes_to_valid_target(self, dict_list, goto_key, rule):
        errors = []

        if 'goto' in rule and goto_key in rule['goto'].keys():
            referenced_id = rule['goto'][goto_key]

            if not self._is_contained_in_list(dict_list, referenced_id):
                invalid_block_error = 'Routing rule routes to invalid {} [{}]'.format(goto_key, referenced_id)
                errors.append(self._error_message(invalid_block_error))
        return errors

    @staticmethod
    def _validate_routing_rules_default(rules, block_or_group):
        """
        Ensure that a set of routing rules contains a default, without a when clause.
        """
        errors = []

        if not rules or all(('goto' not in rule for rule in rules)):
            return errors

        default_routing_rule_count = 0

        for rule in rules:
            rule_directive = rule.get('goto')
            if rule_directive and 'when' not in rule_directive:
                default_routing_rule_count += 1

        if not default_routing_rule_count:
            errors.append(Validator._error_message('The routing rules for group or block: {} must contain a default '
                                                   'routing rule without a when rule'.format(block_or_group['id'])))
        elif default_routing_rule_count > 1:
            errors.append(Validator._error_message('The routing rules for group or block: {} contain multiple default '
                                                   'routing rules. Some of them will not be used'.format(block_or_group['id'])))

        return errors

    def _validate_routing_rule(self, rule, answer_ids_with_group_id, block_or_group):
        errors = []

        rule = rule.get('goto')
        if 'when' in rule:
            errors.extend(self._validate_when_rule(rule['when'], answer_ids_with_group_id, block_or_group['id']))

        return errors

    def _validate_skip_condition(self, skip_condition, answer_ids_with_group_id, block_or_group):
        """
        Validate skip condition is valid
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []
        when = skip_condition.get('when')
        errors.extend(self._validate_when_rule(when, answer_ids_with_group_id, block_or_group['id']))
        return errors

    def _validate_list_answer_references(self, block):
        errors = []

        main_block_questions = self._get_all_questions_for_block(block)
        main_block_ids = {answer['id'] for question in main_block_questions for answer in question['answers']}
        remove_block_questions = self._get_all_questions_for_block(block['remove_block'])
        remove_block_ids = {answer['id'] for question in remove_block_questions for answer in question['answers']}

        if block['add_answer']['id'] not in main_block_ids:
            errors.append(self._error_message(
                'add_answer reference uses id not found in main block question: {}'.format(block['add_answer']['id'])
            ))
        if block['remove_answer']['id'] not in remove_block_ids:
            errors.append(self._error_message(
                'remove_answer reference uses id not found in remove_block: {}'.format(block['remove_answer']['id'])
            ))

        return errors

    def _validate_primary_person_list_answer_references(self, block):

        main_block_questions = self._get_all_questions_for_block(block)
        main_block_ids = {
            answer['id']
            for question in main_block_questions
            for answer in question['answers']
        }

        if block['add_or_edit_answer']['id'] not in main_block_ids:
            return [self._error_message(
                f'add_or_edit_answer reference uses id not found in main block question: {block["add_or_edit_answer"]["id"]}'
            )]
        return []

    def _validate_list_collector(self, block):  # noqa: C901  pylint: disable=too-complex, too-many-locals
        errors = []
        collector_questions = self._get_all_questions_for_block(block)
        errors.extend(self._validate_list_answer_references(block))
        remove_questions = self._get_all_questions_for_block(block['remove_block'])
        add_answer_value = block['add_answer']['value']
        remove_answer_value = block['remove_answer']['value']

        for collector_question in collector_questions:
            for collector_answer in collector_question['answers']:
                if collector_answer['type'] != 'Radio':
                    errors.append(self._error_message('The list collector block {} does not contain a Radio answer type'
                                                      .format(block['id'])))

                if not self._options_contain_value(collector_answer['options'], add_answer_value):
                    errors.append(
                        self._error_message('The list collector block {} has an add_answer_value that is not present in the answer values'
                                            .format(block['id'])))

        for remove_question in remove_questions:
            for remove_answer in remove_question['answers']:
                if remove_answer['type'] != 'Radio':
                    errors.append(self._error_message('The list collector remove block {} does not contain a Radio answer type'
                                                      .format(block['id'])))

                if not self._options_contain_value(remove_answer['options'], remove_answer_value):
                    errors.append(
                        self._error_message('The list collector block {} has a remove_answer_value that is not present in the answer values'
                                            .format(block['id'])))

        nested_blocks = [('add_block', 'ListAddQuestion'), ('edit_block', 'ListEditQuestion'), ('remove_block', 'ListRemoveQuestion')]
        for nested_block_name, nested_block_type in nested_blocks:
            nested_block = block[nested_block_name]
            if nested_block['type'] != nested_block_type:
                errors.append(self._error_message(
                    f'The type of the {nested_block_name} is incorrect for a nested ListCollector block. '
                    f'Expected: {nested_block_type}'))
            if 'routing_rules' in nested_block:
                errors.append(self._error_message(f'The list collector block {block["id"]} contains routing rules '
                                                  f'on the {nested_block["id"]} sub block'))

        errors.extend(self._validate_list_collector_answer_ids(block))

        return errors

    def _validate_primary_person_list_collector(self, block):  # noqa: C901  pylint: disable=too-complex, too-many-locals
        errors = []
        collector_questions = self._get_all_questions_for_block(block)
        errors.extend(self._validate_primary_person_list_answer_references(block))
        add_or_edit_answer_value = block['add_or_edit_answer']['value']

        for collector_question in collector_questions:
            for collector_answer in collector_question['answers']:
                if collector_answer['type'] != 'Radio':
                    errors.append(self._error_message(f'The primary person list collector block {block["id"]} does not contain a Radio answer type'))

                if not self._options_contain_value(collector_answer['options'], add_or_edit_answer_value):
                    errors.append(
                        self._error_message(f'The primary person list collector block {block["id"]} has an add_or_edit_answer value that is not '
                                            'present in the answer values'))

        nested_block = block['add_or_edit_block']
        if nested_block['type'] != 'PrimaryPersonListAddOrEditQuestion':
            errors.append(self._error_message('The type of the add_or_edit_block is incorrect for a nested '
                                              'PrimaryPersonListCollector block. '
                                              'Expected: PrimaryPersonListAddOrEditQuestion'))
        if 'routing_rules' in nested_block:
            errors.append(self._error_message(f'The primary person list collector block {block["id"]} contains routing rules '
                                              f'on the {nested_block["id"]} sub block'))

        errors.extend(self._validate_primary_person_list_collector_answer_ids(block))

        return errors

    def _validate_list_collector_answer_ids(self, block):
        """
        - Ensure that answer_ids on add blocks match between all blocks that populate a single list.
        - Enforce the same answer_ids on add and edit sub-blocks
        """
        errors = []
        list_name = block['populates_list']

        add_block_questions = self._get_all_questions_for_block(block['add_block'])
        edit_block_questions = self._get_all_questions_for_block(block['edit_block'])

        add_answer_ids = {answer['id'] for question in add_block_questions for answer in question['answers']}

        edit_answer_ids = {answer['id'] for question in edit_block_questions for answer in question['answers']}

        existing_add_ids = self._list_collector_answer_ids.get(list_name)

        if not existing_add_ids:
            self._list_collector_answer_ids[list_name] = add_answer_ids
        else:
            difference = add_answer_ids.symmetric_difference(existing_add_ids)
            if difference:
                errors.append(self._error_message('Multiple list collectors populate the list: {} using different answer_ids in the add block'
                                                  .format(list_name)))

        if add_answer_ids.symmetric_difference(edit_answer_ids):
            errors.append(self._error_message('The list collector block {} contains an add block and edit block with different answer ids'
                                              .format(block['id'])))

        return errors

    def _validate_primary_person_list_collector_answer_ids(self, block):
        """
        - Ensure that answer_ids on add blocks match between all blocks that populate a single list.
        """
        errors = []
        list_name = block['populates_list']

        add_or_edit_block_questions = self._get_all_questions_for_block(block['add_or_edit_block'])

        add_answer_ids = {answer['id'] for question in add_or_edit_block_questions for answer in question['answers']}

        existing_add_ids = self._list_collector_answer_ids.get(list_name)

        if not existing_add_ids:
            self._list_collector_answer_ids[list_name] = add_answer_ids
        else:
            difference = add_answer_ids.symmetric_difference(existing_add_ids)
            if difference:
                errors.append(self._error_message(f'Multiple primary person list collectors populate the list: {list_name} using different answer '
                                                  'ids in the add_or_edit block'))

        return errors

    @staticmethod
    def _options_contain_value(options, value):
        for option in options:
            if option['value'] == value:
                return True

    def _validate_calculated_summary_type(self, block, answers_with_parent_ids):
        answers_to_calculate = block['calculation']['answers_to_calculate']

        try:
            answer_types = [
                answers_with_parent_ids[answer_id]['answer']['type']
                for answer_id in answers_to_calculate
            ]
        except KeyError as e:
            return [self._error_message(
                "Invalid answer id {} in block {}'s answers_to_calculate".format(e, block['id']))]

        duplicates = {answer for answer in answers_to_calculate if answers_to_calculate.count(answer) > 1}
        if duplicates:
            return [self._error_message(
                "Duplicate answers: {} in block {}'s answers_to_calculate".format(duplicates, block['id']))]

        if not all(answer_type == answer_types[0] for answer_type in answer_types):
            return [self._error_message(
                "All answers in block {}'s answers_to_calculate must be of the same type".format(block['id']))]

        if answer_types[0] == 'Unit':
            unit_types = [
                answers_with_parent_ids[answer_id]['answer']['unit']
                for answer_id in answers_to_calculate
            ]
            if not all(unit_type == unit_types[0] for unit_type in unit_types):
                return [self._error_message(
                    "All answers in block {}'s answers_to_calculate must be of the same unit".format(block['id']))]

        if answer_types[0] == 'Currency':
            currency_types = [
                answers_with_parent_ids[answer_id]['answer']['currency']
                for answer_id in answers_to_calculate
            ]
            if not all(currency_type == currency_types[0] for currency_type in currency_types):
                return [self._error_message(
                    "All answers in block {}'s answers_to_calculate must be of the same currency".format(block['id']))]

        return []

    def _validate_routing_on_answer_options(self, block, answer):
        answer_errors = []
        if 'routing_rules' in block and block['routing_rules'] and 'options' in answer:
            options = [option['value'] for option in answer['options']]
            has_default_route = False

            for rule in block['routing_rules']:
                if 'goto' in rule and 'when' in rule['goto'].keys():
                    when_clause = rule['goto']['when']
                    for when in when_clause:
                        if 'id' in when and 'value' in when:
                            if when['id'] == answer['id'] and when['value'] in options:
                                options.remove(when['value'])
                else:
                    options = []
                    has_default_route = True

            has_unrouted_options = options and len(options) != len(answer['options'])

            if answer['mandatory'] is False and not has_default_route:
                default_route_not_defined = 'Default route not defined for optional question [{}]'.format(answer['id'])
                answer_errors.append(self._error_message(default_route_not_defined))

            if has_unrouted_options:
                unrouted_error_template = 'Routing rule not defined for all answers or default not defined ' \
                                          'for answer [{}] missing options {}'
                unrouted_error = unrouted_error_template.format(answer['id'], options)
                answer_errors.append(self._error_message(unrouted_error))
        return answer_errors

    def _validate_when_rule(self, when_clause, answer_ids_with_group_id, referenced_id):
        """
        Validates any answer id in a when clause exists within the schema
        Will also check that comparison_id exists
        """
        errors = []

        for when in when_clause:
            if 'list' in when:
                errors.extend(self._validate_list_name_in_when_rule(when))
                break

            answer_errors = self._validate_answer_ids_present_in_schema(when, answer_ids_with_group_id, referenced_id)
            if answer_errors:
                errors.extend(answer_errors)
                break

            # We know the ids are correct, so can continue to perform validation
            errors.extend(self._validate_checkbox_exclusive_conditions_in_when_rule(when, answer_ids_with_group_id))

            if 'comparison_id' in when:
                errors.extend(self._validate_comparison_id_in_when_rule(when, answer_ids_with_group_id, referenced_id))

        return errors

    def _validate_answer_ids_present_in_schema(self, when, answer_ids_with_group_id, referenced_id):
        """
        Validates that any ids that are referenced within the when rule are present within the schema.  This prevents writing
        when conditions against id's that don't exist.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []
        answer_reference_id_fields = ('id', 'comparison_id')
        present_id_ref_keys = [x for x in answer_reference_id_fields if x in when]

        for id_ref_key in present_id_ref_keys:
            if when[id_ref_key] not in answer_ids_with_group_id:
                errors.append(self._error_message('The answer id - {} in the {} key of the "when" clause for {} does not exist'
                                                  .format(when[id_ref_key], id_ref_key, referenced_id)))

        return errors

    def _validate_checkbox_exclusive_conditions_in_when_rule(self, when, answer_ids_with_group_id):
        """
        Validate checkbox exclusive conditions are only used when answer type is Checkbox
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []

        condition = when['condition']
        checkbox_exclusive_conditions = ('contains any', 'contains all', 'contains',
                                         'not contains')
        all_checkbox_conditions = checkbox_exclusive_conditions + ('set', 'not set')
        answer_type = answer_ids_with_group_id[when['id']]['answer']['type'] if 'id' in when else None

        if answer_type == 'Checkbox':
            if condition not in all_checkbox_conditions:
                errors.append(
                    self._error_message(f'The condition `{condition}` cannot be used'
                                        ' with `Checkbox` answer type.',
                                        answer_ids_with_group_id[
                                            when['id']]['answer']['id']))
        elif condition in checkbox_exclusive_conditions:
            errors.append(
                self._error_message(f'The condition `{condition}` can only be used with'
                                    ' `Checkbox` answer types. '
                                    f'Found answer type: {answer_type}',
                                    answer_ids_with_group_id[
                                        when['id']]['answer']['id']))

        return errors

    def _validate_comparison_id_in_when_rule(self, when, answer_ids_with_group_id, referenced_id):
        """
        Validate that conditions requiring list match values define a comparison answer id that is of type Checkbox
        and ensure all other conditions with comparison id match answer types
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []

        answer_id, comparison_id, condition = when['id'], when['comparison_id'], when['condition']
        comparison_answer_type = answer_ids_with_group_id[when['comparison_id']]['answer']['type']
        id_answer_type = answer_ids_with_group_id[when['id']]['answer']['type']
        conditions_requiring_list_match_values = ('equals any', 'not equals any', 'contains any', 'contains all')

        if condition in conditions_requiring_list_match_values:
            if comparison_answer_type != 'Checkbox':
                errors.append(self._error_message(
                    f'The comparison_id `{comparison_id}` is not of answer type `Checkbox`. '
                    f'The condition `{condition}` can only reference `Checkbox` answers when using `comparison id`'))

        elif comparison_answer_type != id_answer_type:
            errors.append(self._error_message(f'The answers used as comparison_id `{comparison_id}` and answer_id `{answer_id}` in the `when` '
                                              f'clause for `{referenced_id}` have different types'))

        return errors

    def _validate_list_name_in_when_rule(self, when):
        """
        Validate that the list referenced in the when rule is defined in the schema
        """
        errors = []
        list_name = when['list']
        if list_name not in self._list_names:
            errors.append(self._error_message(f'The list `{list_name}` is not defined in the schema'))

        return errors

    def _validate_date_range(self, question):
        """
        If period_limits object is present in the DateRange question validates that a date range
        does not have a negative period and days can not be used to define limits for yyyy-mm date ranges
        """
        errors = []

        if question['type'] == 'DateRange' and question.get('period_limits'):
            period_limits = question['period_limits']
            if 'minimum' in period_limits and 'maximum' in period_limits:
                example_date = '2016-05-10'

                # Get minimum and maximum possible dates
                minimum_date = self._get_relative_date(example_date, period_limits['minimum'])
                maximum_date = self._get_relative_date(example_date, period_limits['maximum'])

                if minimum_date > maximum_date:
                    errors.append(self._error_message('The minimum period is greater than the maximum period for {}'
                                                      .format(question['id'])))

            first_answer_type = question['answers'][0]['type']

            has_days_limit = 'days' in period_limits.get('minimum', []) \
                             or 'days' in period_limits.get('maximum', [])
            has_months_limit = 'months' in period_limits.get('minimum', []) \
                               or 'months' in period_limits.get('maximum', [])

            if first_answer_type == 'MonthYearDate' and has_days_limit:
                errors.append(self._error_message('Days can not be used in period_limit for yyyy-mm date range for {}'
                                                  .format(question['id'])))

            if first_answer_type == 'YearDate' and (has_days_limit or has_months_limit):
                errors.append(self._error_message('Days/Months can not be used in period_limit for yyyy date range'
                                                  ' for {}'.format(question['id'])))

        return errors

    def _validate_minimum_and_maximum_offset_date(self, answer):
        # Validates if a date answer has a minimum and maximum
        errors = []

        if 'value' in answer['minimum'] and 'value' in answer['maximum']:
            minimum_date = self._get_offset_date_value(answer['minimum'])
            maximum_date = self._get_offset_date_value(answer['maximum'])

            if minimum_date > maximum_date:
                errors.append(self._error_message('The minimum offset date is greater than the maximum offset date'))

        return errors

    def _validate_numeric_answer_types(self, numeric_answer, answer_ranges):
        """
        Validate numeric answer types are valid.
        :return: list of dictionaries containing error messages, otherwise it returns an empty list
        """
        errors = []

        # Validate referred numeric answer exists (skip further tests for answer if error is returned)
        referred_errors = self._validate_referred_numeric_answer(numeric_answer, answer_ranges)
        errors.extend(referred_errors)
        if referred_errors:
            return errors

        # Validate numeric answer has a positive range of possible responses
        errors.extend(self._validate_numeric_range(numeric_answer, answer_ranges))

        # Validate numeric answer value within system limits
        errors.extend(self._validate_numeric_answer_value(numeric_answer))

        # Validate numeric answer decimal places within system limits
        errors.extend(self._validate_numeric_answer_decimals(numeric_answer))

        # Validate referred numeric answer decimals
        errors.extend(self._validate_referred_numeric_answer_decimals(numeric_answer, answer_ranges))

        # Validate default is only used with non mandatory answers
        errors.extend(self._validate_numeric_default(numeric_answer))

        return errors

    def _validate_numeric_default(self, answer):
        error = []
        if answer.get('mandatory') and answer.get('default') is not None:
            error.append(self._error_message('Default is being used with a mandatory answer: {}'.format(answer['id'])))

        return error

    def _get_numeric_range_values(self, answer, answer_ranges):

        return {
            'min': self._get_answer_minimum(answer, answer_ranges),
            'max': self._get_answer_maximum(answer, answer_ranges),
            'decimal_places': answer.get('decimal_places', 0),
            'min_referred': answer.get('min_value', {}).get('answer_id'),
            'max_referred': answer.get('max_value', {}).get('answer_id'),
            'default': answer.get('default')
        }

    def _validate_duplicates(self, json_to_validate):
        """
        question_id & answer_id should be globally unique with some exceptions:
            - within a block, ids can be duplicated across variants, but must still be unique outside of the block.
            - answer_ids must be duplicated across add / edit blocks on list collectors which populate the same list.
        """

        duplicate_errors = []

        unique_ids_per_block = defaultdict(set)
        non_block_ids = []
        all_ids = []

        for path, value in self._parse_values(json_to_validate, 'id'):
            if 'blocks' in path:
                # Generate a string path and add it to the set representing the ids in that path
                path_list = path.split('/')

                block_path = path_list[:path_list.index('blocks') + 2]

                string_path = '/'.join(block_path)
                # Since unique_ids_per_block is a set, duplicate ids will only be recorded once within the block.
                unique_ids_per_block[string_path].add(value)
            else:
                non_block_ids.append(value)

        for block_ids in unique_ids_per_block.values():
            all_ids.extend(block_ids)

        all_ids.extend(non_block_ids)

        duplicates = Validator._find_duplicates(all_ids)

        for duplicate in duplicates:
            duplicate_errors.append(
                self._error_message('Duplicate id found: {}'.format(duplicate)))

        return duplicate_errors

    @staticmethod
    def _find_duplicates(values):
        """ Yield any elements in the input iterator which occur more than once
        """
        seen = set()
        for item in values:
            if item in seen:
                yield item
            seen.add(item)

    def _validate_duplicate_options(self, answer):
        errors = []

        labels = set()
        values = set()

        for option in answer.get('options', []):

            # labels can have placeholders in, in which case we won't know if they are a duplicate or not
            if isinstance(option['label'], dict):
                continue

            if option['label'] in labels:
                errors.append(self._error_message('Duplicate label found - {}'.format(option['label'])))

            if option['value'] in values:
                errors.append(self._error_message('Duplicate value found - {}'.format(option['value'])))

            labels.add(option['label'])
            values.add(option['value'])

        return errors

    def _validate_schema_contains_submission_page(self, schema, last_block):
        """
        Validate that the final block is of type Summary or Confirmation.
        :param last_block: The final block in the schema
        :return: List of dictionaries containing error messages, otherwise it returns an empty list
        """
        is_last_block_valid = last_block['type'] in {'Summary', 'Confirmation'}
        is_hub_enabled = schema.get('hub', {}).get('enabled')

        if is_last_block_valid and is_hub_enabled:
            return [self._error_message('Schema can only contain one of [Confirmation page, Summary page, Hub page]')]

        if not is_last_block_valid and not is_hub_enabled:
            return [self._error_message('Schema must contain one of [Confirmation page, Summary page, Hub page]')]

        return []

    @staticmethod
    def _error_message(message, ref=None):
        error = {'message': f'Schema Integrity Error. {message}'}
        if isinstance(ref, str):
            error['id'] = ref
        return error

    def _get_answer_minimum(self, answer, answer_ranges):
        defined_minimum = answer.get('min_value')
        minimum_values = self._get_defined_numeric_value(defined_minimum, 0, answer_ranges)
        minimum_values = self._convert_numeric_values_to_exclusive(defined_minimum, minimum_values,
                                                                   'min', answer.get('decimal_places', 0))

        return minimum_values

    def _get_answer_maximum(self, answer, answer_ranges):
        defined_maximum = answer.get('max_value')
        maximum_values = self._get_defined_numeric_value(defined_maximum, MAX_NUMBER, answer_ranges)
        maximum_values = self._convert_numeric_values_to_exclusive(defined_maximum, maximum_values,
                                                                   'max', answer.get('decimal_places', 0))

        return maximum_values

    @staticmethod
    def _get_defined_numeric_value(defined_value, system_default, answer_ranges):
        values = None

        if defined_value is None:
            values = [system_default]
        elif 'value' in defined_value:
            values = [defined_value.get('value')]
        elif 'answer_id' in defined_value:
            referred_answer = answer_ranges.get(defined_value['answer_id'])
            if referred_answer is None:
                values = None  # Referred answer is not  valid (picked up by _validate_referred_numeric_answer)
            elif referred_answer.get('default') is not None:
                values = [system_default]
            else:
                values = referred_answer['min'] + referred_answer['max']

        return values

    @staticmethod
    def _convert_numeric_values_to_exclusive(defined_value, values, min_or_max, decimal_places):
        exclusive_values = values
        if defined_value and defined_value.get('exclusive') and values:
            exclusive_values = []
            for value in values:
                if min_or_max == 'min':
                    exclusive_values.append(value + (1 / 10 ** decimal_places))
                else:
                    exclusive_values.append(value - (1 / 10 ** decimal_places))

        return exclusive_values

    def _validate_referred_numeric_answer(self, answer, answer_ranges):
        """
        Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        If either of the above is true then it will not have been given a value by _get_numeric_range_values
        """
        errors = []
        if answer_ranges[answer.get('id')]['min'] is None:
            error_message = 'The referenced answer "{}" can not be used to set the minimum of answer "{}"' \
                .format(answer['min_value']['answer_id'], answer['id'])
            errors.append(self._error_message(error_message))
        if answer_ranges[answer.get('id')]['max'] is None:
            error_message = 'The referenced answer "{}" can not be used to set the maximum of answer "{}"' \
                .format(answer['max_value']['answer_id'], answer['id'])
            errors.append(self._error_message(error_message))

        return errors

    def _validate_numeric_range(self, answer, answer_ranges):
        errors = []
        for max_value in answer_ranges[answer.get('id')]['max']:
            for min_value in answer_ranges[answer.get('id')]['min']:
                if max_value - min_value < 0:
                    error_message = 'Invalid range of min = {} and max = {} is possible for answer "{}".' \
                        .format(min_value, max_value, answer['id'])
                    errors.append(self._error_message(error_message))

        return errors

    def _validate_numeric_answer_value(self, answer):
        errors = []
        if answer.get('min_value') and answer['min_value'].get('value', 0) < MIN_NUMBER:
            error_message = 'Minimum value {} for answer "{}" is less than system limit of {}' \
                .format(answer['min_value']['value'], answer['id'], MIN_NUMBER)
            errors.append(self._error_message(error_message))

        if answer.get('max_value') and answer['max_value'].get('value', 0) > MAX_NUMBER:
            error_message = 'Maximum value {} for answer "{}" is greater than system limit of {}' \
                .format(answer['max_value']['value'], answer['id'], MAX_NUMBER)
            errors.append(self._error_message(error_message))

        return errors

    def _validate_numeric_answer_decimals(self, answer):
        errors = []
        if answer.get('decimal_places', 0) > MAX_DECIMAL_PLACES:
            error_message = 'Number of decimal places {} for answer "{}" is greater than system limit of {}' \
                .format(answer['decimal_places'], answer['id'], MAX_DECIMAL_PLACES)
            errors.append(self._error_message(error_message))

        return errors

    def _validate_referred_numeric_answer_decimals(self, answer, answer_ranges):
        errors = []
        answer_values = answer_ranges[answer['id']]

        if answer_values['min_referred'] is not None:
            referred_values = answer_ranges[answer_values['min_referred']]
            if answer_values['decimal_places'] < referred_values['decimal_places']:
                error_message = 'The referenced answer "{}" has a greater number of decimal places than answer "{}"' \
                    .format(answer_values['min_referred'], answer['id'])
                errors.append(self._error_message(error_message))

        if answer_values['max_referred'] is not None:
            referred_values = answer_ranges[answer_values['max_referred']]
            if answer_values['decimal_places'] < referred_values['decimal_places']:
                error_message = 'The referenced answer "{}" has a greater number of decimal places than answer "{}"' \
                    .format(answer_values['max_referred'], answer['id'])
                errors.append(self._error_message(error_message))

        return errors

    def _validate_mutually_exclusive(self, question):
        errors = []

        if question['type'] == 'MutuallyExclusive':
            answers = question['answers']

            if any(answer['mandatory'] is True for answer in answers):
                errors.append(self._error_message('MutuallyExclusive question type cannot contain mandatory answers.'))

            if answers[-1]['type'] != 'Checkbox':
                errors.append(self._error_message('{} is not of type Checkbox.'.format(answers[-1]['id'])))

        return errors

    def _validate_totaliser_defines_decimal_places(self, answer):
        errors = []

        if 'calculated' in answer and ('decimal_places' not in answer or answer['decimal_places'] != 2):
            errors.append(self._error_message("'decimal_places' must be defined and set to 2 for the answer_id - {}".format(answer['id'])))

        return errors

    def _get_dicts_with_key(self, input_data, key_name):
        """
        Get all dicts that contain `key_name`.
        :param input_data: the input data to search
        :param key_name: the key to find
        :return: list of dicts containing the key name, otherwise returns None
        """
        if isinstance(input_data, dict):
            for k, v in input_data.items():
                if k == key_name:
                    yield input_data
                else:
                    yield from self._get_dicts_with_key(v, key_name)
        elif isinstance(input_data, list):
            for item in input_data:
                yield from self._get_dicts_with_key(item, key_name)

    def _validate_placeholders(self, block_json, answers_with_parent_ids, valid_metadata_ids):
        errors = []
        strings_with_placeholders = self._get_dicts_with_key(block_json, 'placeholders')
        for string_with_placeholders in strings_with_placeholders or []:
            regex = re.compile('{(.*?)}')
            placeholders_in_string = regex.findall(string_with_placeholders.get('text'))
            placeholder_definition_names = []
            for placeholder_definition in string_with_placeholders.get('placeholders'):
                placeholder_definition_names.append(placeholder_definition['placeholder'])

                transforms = placeholder_definition.get('transforms')
                answer_ids_to_validate, metadata_ids_to_validate = self._get_placeholder_source_ids(placeholder_definition, transforms)

                errors.extend(self._validate_placeholder_answer_ids(block_json['id'], placeholder_definition,
                                                                    answers_with_parent_ids, answer_ids_to_validate))
                errors.extend(self._validate_placeholder_metadata_ids(valid_metadata_ids, metadata_ids_to_validate,
                                                                      placeholder_definition['placeholder']))

                if transforms:
                    errors.extend(self._validate_placeholder_transforms(transforms, block_json['id']))

            if sorted(placeholders_in_string) != sorted(placeholder_definition_names):
                errors.append(self._error_message(
                    "Placeholders in 'text' doesn't match 'placeholders' definition for block id '{}'".format(
                        block_json['id'])))

        return errors

    @staticmethod
    def _get_placeholder_source_ids(placeholder_definition, transforms):

        answer_ids_to_validate = []
        metadata_ids_to_validate = []

        if transforms:
            for transform in transforms:
                for argument in transform['arguments'].values():
                    if 'source' in argument and argument['source'] == 'answers':
                        if isinstance(argument['identifier'], list):
                            answer_ids_to_validate.extend(argument['identifier'])
                        else:
                            answer_ids_to_validate.append(argument['identifier'])

                    if 'source' in argument and argument['source'] == 'metadata':
                        if isinstance(argument['identifier'], list):
                            metadata_ids_to_validate.extend(argument['identifier'])
                        else:
                            metadata_ids_to_validate.append(argument['identifier'])

        if 'value' in placeholder_definition and 'source' in placeholder_definition['value'] and \
                placeholder_definition['value']['source'] == 'answers':
            answer_ids_to_validate.append(placeholder_definition['value']['identifier'])

        if 'value' in placeholder_definition and 'source' in placeholder_definition['value'] and \
                placeholder_definition['value']['source'] == 'metadata':
            metadata_ids_to_validate.append(placeholder_definition['value']['identifier'])

        return answer_ids_to_validate, metadata_ids_to_validate

    def _validate_placeholder_answer_ids(self, block_id, placeholder_definition, answers_with_parent_ids, answer_ids_to_validate):
        errors = []

        for answer_id_to_validate in answer_ids_to_validate:
            if answer_id_to_validate not in answers_with_parent_ids:
                errors.append(self._error_message('Invalid answer id reference `{}` for placeholder `{}`'.format(
                    answer_id_to_validate,
                    placeholder_definition['placeholder']
                )))
                continue
            answer_block_id = answers_with_parent_ids[answer_id_to_validate]['block']
            if answer_block_id == block_id:
                errors.append(self._error_message('Invalid answer id reference `{}` for placeholder `{}` (self-reference)'.format(
                    answer_id_to_validate,
                    placeholder_definition['placeholder']
                )))
        return errors

    def _validate_placeholder_metadata_ids(self, valid_metadata_ids, metadata_ids_to_validate, placeholder_name):
        errors = []

        for metadata_id_to_validate in metadata_ids_to_validate:
            if metadata_id_to_validate not in valid_metadata_ids:
                errors.append(self._error_message('Invalid metadata reference `{}` for placeholder `{}`'.format(
                    metadata_id_to_validate,
                    placeholder_name
                )))

        return errors

    def _validate_placeholder_transforms(self, transforms, block_id):
        errors = []

        # First transform can't reference a previous transform
        first_transform = transforms[0]
        for argument_name in first_transform.get('arguments'):
            argument = first_transform['arguments'][argument_name]
            if isinstance(argument, dict) and argument.get('source') == 'previous_transform':
                errors.append(self._error_message(
                    "Can't reference `previous_transform` in a first transform in block id '{}'".format(
                        block_id)))

        # Previous transform must be referenced in all subsequent transforms
        for transform in transforms[1:]:
            previous_transform_used = False
            for argument_name in transform.get('arguments'):
                argument = transform['arguments'][argument_name]
                if isinstance(argument, dict) and argument.get('source') == 'previous_transform':
                    previous_transform_used = True

            if not previous_transform_used:
                errors.append(self._error_message(
                    "`previous_transform` not referenced in chained transform in block id '{}'".format(
                        block_id)))

        return errors

    @staticmethod
    def _is_contained_in_list(dict_list, key_id):
        for dict_to_check in dict_list:
            if dict_to_check['id'] == key_id:
                return True

        return False

    def _parse_values(self, schema_json, parsed_key, path=None):
        """ generate a list of values with a key of `parsed_key`.

        These values will be returned with the json pointer path to them through the object e.g.
            - '/sections/0/groups/0/blocks/1/question_variants/0/question/question-2'

        Returns: generator yielding (path, value) tuples
        """

        if path is None:
            path = ''

        ignored_keys = ['routing_rules', 'skip_conditions', 'when']
        ignored_sub_paths = ['edit_block/question/answers', 'add_block/question/answers', 'remove_block/question/answers']

        for key, value in schema_json.items():
            new_path = f'{path}/{key}'
            if key == parsed_key:
                yield (path, value)
            elif key in ignored_keys:
                continue
            elif any([ignored_path in new_path for ignored_path in ignored_sub_paths]):
                continue
            elif isinstance(value, dict):
                yield from self._parse_values(value, parsed_key, new_path)
            elif isinstance(value, list):
                for index, schema_item in enumerate(value):
                    indexed_path = new_path + f'/{index}'
                    if isinstance(schema_item, dict):
                        yield from self._parse_values(schema_item, parsed_key, indexed_path)

    def _get_offset_date_value(self, answer_min_or_max):
        if answer_min_or_max['value'] == 'now':
            value = datetime.utcnow().strftime('%Y-%m-%d')
        else:
            value = answer_min_or_max['value']

        if 'offset_by' in answer_min_or_max:
            offset = answer_min_or_max['offset_by']
            value = self._get_relative_date(value, offset).strftime('%Y-%m-%d')

        return value

    def _get_relative_date(self, date_string, offset_object):
        # Returns a relative date given an offset or period object
        return self._convert_to_datetime(date_string) + relativedelta(years=offset_object.get('years', 0),
                                                                      months=offset_object.get('months', 0),
                                                                      days=offset_object.get('days', 0))

    @staticmethod
    def _convert_to_datetime(value):
        date_format = '%Y-%m'
        if value and re.match(r'\d{4}-\d{2}-\d{2}', value):
            date_format = '%Y-%m-%d'

        return datetime.strptime(value, date_format) if value else None

    def _get_answers_with_parent_ids(self, json_to_validate):
        answers = {}
        for question, context in self._get_questions_with_context(json_to_validate):
            for answer in question.get('answers', []):
                answers[answer['id']] = {
                    'answer': answer,
                    **context
                }
                for option in answer.get('options', []):
                    detail_answer = option.get('detail_answer')
                    if detail_answer:
                        answers[detail_answer['id']] = {
                            'answer': detail_answer,
                            **context
                        }

        return answers

    def _get_questions_with_context(self, json):
        for section in json.get('sections'):
            for group in section.get('groups'):
                for block in group.get('blocks'):
                    for question in self._get_all_questions_for_block(block):
                        context = {
                            'block': block['id'],
                            'group_id': group['id'],
                            'section': section['id']
                        }
                        yield question, context
                    for sub_block_type in ('add_block', 'edit_block', 'remove_block', 'add_or_edit_block'):
                        sub_block = block.get(sub_block_type)
                        if sub_block:
                            for question in self._get_all_questions_for_block(sub_block):
                                context = {
                                    'block': sub_block['id'],
                                    'group_id': group['id'],
                                    'section': section['id']
                                }
                                yield question, context

    @staticmethod
    def _get_all_questions_for_block(block):
        """ Get all questions on a block including variants"""
        questions = []

        for variant in block.get('question_variants', []):
            questions.append(variant['question'])

        single_question = block.get('question')
        if single_question:
            questions.append(single_question)

        return questions

    @staticmethod
    def _get_list_names(json_to_validate):
        list_names = []
        for section in json_to_validate['sections']:
            for group in section['groups']:
                for block in group['blocks']:
                    if block['type'] == 'ListCollector':
                        list_names.append(block['populates_list'])
        return list_names

    class CoreStructureError(Exception):
        def __init__(self, message):
            super().__init__()
            self.message = message
