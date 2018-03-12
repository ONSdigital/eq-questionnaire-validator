import itertools
from json import load
import os
import pathlib

from jsonschema import SchemaError, RefResolver, validate, ValidationError

MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


class Validator:
    def __init__(self):
        with open('schemas/questionnaire_v1.json', encoding='utf8') as schema_data:
            self.schema = load(schema_data)

    def validate_schema(self, json_to_validate):

        schema_errors = self._validate_json_against_schema(json_to_validate)

        if schema_errors:
            return schema_errors

        errors = []

        errors.extend(self.validate_schema_contains_valid_routing_rules(json_to_validate))

        errors.extend(self.validate_calculated_ids_in_answers_to_group_exists(json_to_validate))

        errors.extend(self.validate_routing_rules_has_default_if_not_all_answers_routed(json_to_validate))

        errors.extend(self.validate_numeric_answer_types(json_to_validate))

        ignored_keys = ['routing_rules', 'skip_conditions']
        errors.extend(self.validate_duplicates(json_to_validate, ignored_keys, 'id'))
        errors.extend(self.validate_duplicates(json_to_validate, ignored_keys, 'alias'))

        errors.extend(self.validate_duplicate_options(json_to_validate))

        errors.extend(self.validate_contains_confirmation_or_summary(json_to_validate))

        errors.extend(self.validate_child_answers_define_parent(json_to_validate))

        return errors

    def _validate_json_against_schema(self, json_to_validate):
        try:
            base_uri = pathlib.Path(os.path.abspath('schemas/questionnaire_v1.json')).as_uri()
            resolver = RefResolver(base_uri=base_uri, referrer=self.schema)
            validate(json_to_validate, self.schema, resolver=resolver)
            return []
        except ValidationError as e:
            return {
                'message': e.message,
                'path': str(e.path),
            }
        except SchemaError as e:
            return '{}'.format(e)

    def validate_calculated_ids_in_answers_to_group_exists(self, json_to_validate):
        # Validates that any answer ids within the 'answer_to_group'
        # list are existing answers within the question

        errors = []

        for question in self._get_questions(json_to_validate):
            if question['type'] == 'Calculated':
                answer_ids = [answer['id'] for answer in question.get('answers')]
                calculated_question = question.get('calculated')
                for answer_id in calculated_question['answers_to_group']:
                    if answer_id not in answer_ids:
                        invalid_answer_id_error = 'Answer id - {} does not exist within this question - {}'\
                            .format(answer_id, question['id'])
                        errors.append(self._error_message(invalid_answer_id_error))

        return errors

    def validate_schema_contains_valid_routing_rules(self, json_to_validate):

        errors = []

        blocks = self._get_blocks(json_to_validate)
        for block in blocks:
            if 'routing_rules' in block and block['routing_rules']:
                for rule in block['routing_rules']:
                    if 'goto' in rule and 'id' in rule['goto'].keys():
                        block_id = rule['goto']['id']
                        if block_id == 'summary':
                            continue

                        if not self._contains_block(json_to_validate, block_id):
                            invalid_block_error = 'Routing rule routes to invalid block [{}]'.format(block_id)
                            errors.append(self._error_message(invalid_block_error))

                    if 'goto' in rule and 'group' in rule['goto'].keys():
                        group_id = rule['goto']['group']

                        if not self._contains_group(json_to_validate, group_id):
                            invalid_group_error = 'Routing rule routes to invalid group [{}]'.format(group_id)
                            errors.append(self._error_message(invalid_group_error))

        return errors

    def validate_routing_rules_has_default_if_not_all_answers_routed(self, json_to_validate):

        errors = []

        for block in self._get_blocks(json_to_validate):
            for question in block.get('questions', []):
                for answer in question.get('answers', []):
                    errors.extend(self.validate_answer(block, answer))

        return errors

    def validate_answer(self, block, answer):
        answer_errors = []
        if 'routing_rules' in block and block['routing_rules'] and 'options' in answer:
            options = [option['value'] for option in answer['options']]
            has_default_route = False

            for rule in block['routing_rules']:
                if 'goto' in rule and 'when' in rule['goto'].keys():
                    when = rule['goto']['when']
                    if 'id' in when and when['id'] == answer['id'] and when['value'] in options:
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

    def validate_numeric_answer_types(self, json_to_validate):
        errors = []
        answer_ranges = {}

        numeric_answers = (
            answer for answer in self._get_answers(json_to_validate)
            if answer['type'] in ['Number', 'Currency', 'Percentage']
        )

        for answer in numeric_answers:
            answer_ranges[answer.get('id')] = self._get_numeric_range_values(answer, answer_ranges)

            # Validate referred numeric answer exists (skip further tests for answer if error is returned)
            referred_errors = self._validate_referred_numeric_answer(answer, answer_ranges)
            errors.extend(referred_errors)
            if referred_errors:
                continue

            # Validate numeric answer has a positive range of possible responses
            errors.extend(self._validate_numeric_range(answer, answer_ranges))

            # Validate numeric answer value within system limits
            errors.extend(self._validate_numeric_answer_value(answer))

            # Validate numeric answer decimal places within system limits
            errors.extend(self._validate_numeric_answer_decimals(answer))

            # Validate referred numeric answer decimals
            errors.extend(self._validate_referred_numeric_answer_decimals(answer, answer_ranges))

        return errors

    def _get_numeric_range_values(self, answer, answer_ranges):

        return {
            'min': self._get_answer_minimum(answer, answer_ranges),
            'max': self._get_answer_maximum(answer, answer_ranges),
            'decimal_places': answer.get('decimal_places', 0),
            'min_referred': answer.get('min_value', {}).get('answer_id'),
            'max_referred': answer.get('max_value', {}).get('answer_id'),
        }

    def validate_duplicates(self, json_to_validate, ignored_keys, special_key):
        unique_items = []
        duplicate_errors = []

        for value in self._parse_values(json_to_validate, ignored_keys, special_key):
            if value in unique_items:
                duplicate_errors.append(self._error_message('Duplicate {} found. value {}'.format(special_key, value)))
            else:
                unique_items.append(value)

        return duplicate_errors

    def validate_duplicate_options(self, json_to_validate):
        errors = []

        for block in self._get_blocks(json_to_validate):
            answers_for_block = self._get_answers_for_block(block)

            for answers in answers_for_block:
                labels = set()
                values = set()

                for option in answers.get('options', []):

                    if option['label'] in labels:
                        errors.append(self._error_message('Duplicate label found - {}'.format(option['label'])))

                    if option['value'] in values:
                        errors.append(self._error_message('Duplicate value found - {}'.format(option['value'])))

                    labels.add(option['label'])
                    values.add(option['value'])

        return errors

    def validate_contains_confirmation_or_summary(self, json_to_validate):
        blocks = self._get_blocks(json_to_validate)
        for block in blocks:
            if block['type'] in ['Summary', 'Confirmation']:
                return []

        return [self._error_message('Schemas does not have a confirmation or summary page')]

    def validate_child_answers_define_parent(self, json_to_validate):
        errors = []

        for block in self._get_blocks(json_to_validate):
            answers_by_id = self._get_answers_by_id_for_block(block)

            for answer_id, answer in answers_by_id.items():
                if answer['type'] in ['Radio', 'Checkbox']:
                    child_answer_ids = (o['child_answer_id'] for o in answer['options'] if 'child_answer_id' in o
                                        and o['child_answer_id'])

                    for child_answer_id in child_answer_ids:
                        if child_answer_id not in answers_by_id:
                            errors.extend([self._error_message('Child answer with id %s does not exist in schemas'
                                                               % child_answer_id)])
                            continue
                        if 'parent_answer_id' not in answers_by_id[child_answer_id]:
                            errors.extend([self._error_message('Child answer %s does not define parent_answer_id %s '
                                                               'in schemas' % (child_answer_id, answer_id))])
                            continue
                        if answers_by_id[child_answer_id]['parent_answer_id'] != answer_id:
                            errors.extend([self._error_message('Child answer %s defines incorrect parent_answer_id %s '
                                                               'in schemas: Should be %s'
                                                               % (child_answer_id,
                                                                  answers_by_id[child_answer_id]['parent_answer_id'],
                                                                  answer_id))])
                            continue

        return errors

    @classmethod
    def _get_answers(cls, survey_json):
        return itertools.chain.from_iterable(
            question.get('answers', []) for question in cls._get_questions(survey_json)
        )

    @classmethod
    def _get_questions(cls, survey_json):
        return itertools.chain.from_iterable(
            block.get('questions', []) for block in cls._get_blocks(survey_json)
        )

    @classmethod
    def _get_blocks(cls, survey_json):
        return itertools.chain.from_iterable(
            group.get('blocks', []) for group in cls._get_groups(survey_json)
        )

    @classmethod
    def _get_groups(cls, survey_json):
        return itertools.chain.from_iterable(
            section.get('groups', []) for section in survey_json['sections']
        )

    @staticmethod
    def _get_answers_by_id_for_block(block_json):
        answers = {}
        for question_json in block_json.get('questions', []):
            for answer_json in question_json['answers']:
                answers[answer_json['id']] = answer_json
        return answers

    @staticmethod
    def _error_message(message):
        return {'message': 'Schema Integrity Error. {}'.format(message)}

    @staticmethod
    def _get_answers_for_block(block_json):
        answers = []
        for question_json in block_json.get('questions', []):
            for answer_json in question_json['answers']:
                answers.append(answer_json)
        return answers

    def _get_answer_minimum(self, answer, answer_ranges):
        defined_minimum = answer.get('min_value')
        minimum_values = self.get_defined_numeric_value(defined_minimum, 0, answer_ranges)
        minimum_values = self._convert_numeric_values_to_exclusive(defined_minimum, minimum_values,
                                                                   'min', answer.get('decimal_places', 0))

        return minimum_values

    def _get_answer_maximum(self, answer, answer_ranges):
        defined_maximum = answer.get('max_value')
        maximum_values = self.get_defined_numeric_value(defined_maximum, MAX_NUMBER, answer_ranges)
        maximum_values = self._convert_numeric_values_to_exclusive(defined_maximum, maximum_values,
                                                                   'max', answer.get('decimal_places', 0))

        return maximum_values

    @staticmethod
    def get_defined_numeric_value(defined_value, system_default, answer_ranges):
        values = None

        if defined_value is None:
            values = [system_default]
        elif 'value' in defined_value:
            values = [defined_value.get('value')]
        elif 'answer_id' in defined_value:
            referred_answer = answer_ranges.get(defined_value['answer_id'])
            if referred_answer is None:
                values = None  # Referred answer is not  valid (picked up by _validate_referred_numeric_answer)
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
        # Referred will only be in answer_ranges if it's of a numeric type and appears earlier in the schema
        # If either of the above is true then it will not have been given a value by _get_numeric_range_values
        errors = []
        if answer_ranges[answer.get('id')]['min'] is None:
            error_message = 'The referenced answer "{}" can not be used to set the minimum of answer "{}"'\
                .format(answer['min_value']['answer_id'], answer['id'])
            errors.append(self._error_message(error_message))
        if answer_ranges[answer.get('id')]['max'] is None:
            error_message = 'The referenced answer "{}" can not be used to set the maximum of answer "{}"'\
                .format(answer['max_value']['answer_id'], answer['id'])
            errors.append(self._error_message(error_message))

        return errors

    def _validate_numeric_range(self, answer, answer_ranges):
        errors = []
        for max_value in answer_ranges[answer.get('id')]['max']:
            for min_value in answer_ranges[answer.get('id')]['min']:
                if max_value - min_value < 0:
                    error_message = 'Invalid range of min = {} and max = {} is possible for answer "{}".'\
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

    def _contains_group(self, json, group_id):
        matching_groups = [g for g in self._get_groups(json) if g['id'] == group_id]
        return len(matching_groups) == 1

    def _contains_block(self, json, block_id):
        matching_blocks = [b for b in self._get_blocks(json) if b['id'] == block_id]
        return len(matching_blocks) == 1

    def _parse_values(self, schema_json, ignored_keys, parsed_key):
        for key, value in schema_json.items():
            if key == parsed_key:
                yield value
            elif key in ignored_keys:
                continue
            elif isinstance(value, dict):
                yield from self._parse_values(value, ignored_keys, parsed_key)
            elif isinstance(value, list):
                for schema_item in value:
                    if isinstance(schema_item, dict):
                        yield from self._parse_values(schema_item, ignored_keys, parsed_key)
