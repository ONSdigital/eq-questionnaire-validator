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

    def validate_schema(self, json_to_validate):  # noqa: C901  pylint: disable=too-complex

        schema_errors = self._validate_json_against_schema(json_to_validate)

        if schema_errors:
            return schema_errors

        errors = []

        numeric_answer_ranges = {}

        all_groups = []
        for section in json_to_validate.get('sections'):
            all_groups.extend(section.get('groups'))

        for section in json_to_validate['sections']:
            for group in section['groups']:
                for block in group['blocks']:

                    if section == json_to_validate['sections'][-1] \
                            and group == section['groups'][-1] \
                            and block == group['blocks'][-1]:
                        errors.extend(self.validate_contains_confirmation_or_summary(block))

                    for rule in block.get('routing_rules', []):
                        errors.extend(self.validate_schema_contains_valid_routing_rules(group['blocks'], 'block', rule))
                        errors.extend(self.validate_schema_contains_valid_routing_rules(all_groups, 'group', rule))

                    for question in block.get('questions', []):

                        errors.extend(self.validate_calculated_ids_in_answers_to_calculate_exists(question))
                        errors.extend(self.validate_child_answers_define_parent(question['answers']))

                        for answer in question['answers']:
                            errors.extend(self.validate_routing_on_answer_options(block, answer))
                            errors.extend(self.validate_duplicate_options(answer))

                            if answer['type'] in ['Number', 'Currency', 'Percentage']:
                                numeric_answer_ranges[answer.get('id')] = self._get_numeric_range_values(answer, numeric_answer_ranges)

                                errors.extend(self.validate_numeric_answer_types(answer, numeric_answer_ranges))

        errors.extend(self.validate_duplicates(json_to_validate))

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

    def validate_calculated_ids_in_answers_to_calculate_exists(self, question):
        # Validates that any answer ids within the 'answer_to_group'
        # list are existing answers within the question

        errors = []

        if question['type'] == 'Calculated':
            answer_ids = [answer['id'] for answer in question.get('answers')]
            for calculation in question.get('calculations'):
                for answer_id in calculation['answers_to_calculate']:
                    if answer_id not in answer_ids:
                        invalid_answer_id_error = 'Answer id - {} does not exist within this question - {}'\
                            .format(answer_id, question['id'])
                        errors.append(self._error_message(invalid_answer_id_error))

        return errors

    def validate_schema_contains_valid_routing_rules(self, dict_list, goto_key, rule):
        errors = []

        if 'goto' in rule and goto_key in rule['goto'].keys():
            referenced_id = rule['goto'][goto_key]

            if not self._is_contained_in_list(dict_list, referenced_id):
                invalid_block_error = 'Routing rule routes to invalid {} [{}]'.format(goto_key, referenced_id)
                errors.append(self._error_message(invalid_block_error))

        return errors

    def validate_routing_on_answer_options(self, block, answer):
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

    def validate_numeric_answer_types(self, numeric_answer, answer_ranges):
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

    def validate_duplicates(self, json_to_validate):
        special_keys = ['id', 'alias']
        duplicate_errors = []

        for special_key in special_keys:
            unique_items = []

            for value in self._parse_values(json_to_validate, special_key):
                if value in unique_items:
                    duplicate_errors.append(self._error_message('Duplicate {} found. value {}'.format(special_key, value)))
                else:
                    unique_items.append(value)

        return duplicate_errors

    def validate_duplicate_options(self, answer):
        errors = []

        labels = set()
        values = set()

        for option in answer.get('options', []):

            if option['label'] in labels:
                errors.append(self._error_message('Duplicate label found - {}'.format(option['label'])))

            if option['value'] in values:
                errors.append(self._error_message('Duplicate value found - {}'.format(option['value'])))

            labels.add(option['label'])
            values.add(option['value'])

        return errors

    def validate_contains_confirmation_or_summary(self, last_block):
        if last_block['type'] in ['Summary', 'Confirmation']:
            return []

        return [self._error_message('Schemas does not have a confirmation or summary page')]

    def validate_child_answers_define_parent(self, answers):
        errors = []

        answers_by_id = self._get_answers_by_id_for_block(answers)

        for answer in answers:
            if answer['type'] in ['Radio', 'Checkbox']:
                child_answer_ids = (option['child_answer_id'] for option in answer['options']
                                    if 'child_answer_id' in option and option['child_answer_id'])

                for child_answer_id in child_answer_ids:
                    if child_answer_id not in answers_by_id:
                        errors.extend([self._error_message('Child answer with id %s does not exist in schemas'
                                                           % child_answer_id)])
                        continue
                    if 'parent_answer_id' not in answers_by_id[child_answer_id]:
                        errors.extend([self._error_message('Child answer %s does not define parent_answer_id %s '
                                                           'in schemas' % (child_answer_id, answer['id']))])
                        continue
                    if answers_by_id[child_answer_id]['parent_answer_id'] != answer['id']:
                        errors.extend([self._error_message('Child answer %s defines incorrect parent_answer_id %s '
                                                           'in schemas: Should be %s'
                                                           % (child_answer_id,
                                                              answers_by_id[child_answer_id]['parent_answer_id'],
                                                              answer['id']))])
                        continue

        return errors

    @staticmethod
    def _get_answers_by_id_for_block(answers):
        keyed_answers = {}
        for answer_json in answers:
            keyed_answers[answer_json['id']] = answer_json
        return keyed_answers

    @staticmethod
    def _error_message(message):
        return {'message': 'Schema Integrity Error. {}'.format(message)}

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

    @staticmethod
    def _is_contained_in_list(dict_list, key_id):
        for dict_to_check in dict_list:
            if dict_to_check['id'] == key_id:
                return True

        return False

    def _parse_values(self, schema_json, parsed_key):
        ignored_keys = ['routing_rules', 'skip_conditions']

        for key, value in schema_json.items():
            if key == parsed_key:
                yield value
            elif key in ignored_keys:
                continue
            elif isinstance(value, dict):
                yield from self._parse_values(value, parsed_key)
            elif isinstance(value, list):
                for schema_item in value:
                    if isinstance(schema_item, dict):
                        yield from self._parse_values(schema_item, parsed_key)
