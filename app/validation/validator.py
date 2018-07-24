import re
from json import load
import os
import pathlib

from datetime import datetime
from dateutil.relativedelta import relativedelta
from jsonschema import SchemaError, RefResolver, validate, ValidationError
from jsonschema.exceptions import best_match

MAX_NUMBER = 9999999999
MIN_NUMBER = -999999999
MAX_DECIMAL_PLACES = 6


class Validator:
    def __init__(self):
        with open('schemas/questionnaire_v1.json', encoding='utf8') as schema_data:
            self.schema = load(schema_data)

    def validate_schema(self, json_to_validate):  # noqa: C901  pylint: disable=too-complex, too-many-branches

        schema_errors = self._validate_json_against_schema(json_to_validate)

        if schema_errors:
            return schema_errors

        errors = []

        errors.extend(self._validate_schema_contain_metadata(json_to_validate))

        numeric_answer_ranges = {}
        answers_with_parent_ids = self._get_answers_with_parent_ids(json_to_validate)

        all_groups = []
        for section in json_to_validate.get('sections'):
            all_groups.extend(section.get('groups'))

        for section in json_to_validate['sections']:
            for group in section['groups']:

                for rule in group.get('routing_rules', []):
                    errors.extend(self.validate_schema_routing_rule_routes_to_valid_target(group['blocks'], 'block', rule))
                    errors.extend(self.validate_schema_routing_rule_routes_to_valid_target(all_groups, 'group', rule))

                    errors.extend(self.validate_schema_routing_rule_dependent_on_valid_answer(rule, answers_with_parent_ids, group))
                    errors.extend(self.validate_repeat_when_rule_restricted(rule, answers_with_parent_ids, group))

                for block in group['blocks']:

                    if section == json_to_validate['sections'][-1] \
                            and group == section['groups'][-1] \
                            and block == group['blocks'][-1]:
                        errors.extend(self.validate_contains_confirmation_or_summary(block))

                    for rule in block.get('routing_rules', []):
                        errors.extend(self.validate_schema_routing_rule_routes_to_valid_target(group['blocks'], 'block', rule))
                        errors.extend(self.validate_schema_routing_rule_routes_to_valid_target(all_groups, 'group', rule))

                        errors.extend(self.validate_schema_routing_rule_dependent_on_valid_answer(rule, answers_with_parent_ids, block))
                        errors.extend(self.validate_repeat_rule_restricted(rule, block))

                    if block['type'] == 'CalculatedSummary':
                        errors.extend(self.validate_calculated_summary_type(block, answers_with_parent_ids))

                    for question in block.get('questions', []):

                        errors.extend(self.validate_calculated_ids_in_answers_to_calculate_exists(question))
                        errors.extend(self.validate_child_answers_define_parent(question.get('answers', [])))
                        errors.extend(self.validate_date_range(question))
                        if question.get('titles'):
                            errors.extend(self.validate_multiple_question_titles(question['titles'],
                                                                                 question['id'],
                                                                                 answers_with_parent_ids))

                        for answer in question.get('answers', []):
                            errors.extend(self.validate_routing_on_answer_options(block, answer))
                            errors.extend(self.validate_duplicate_options(answer))

                            if answer['type'] == 'Date':
                                if 'minimum' in answer and 'maximum' in answer:
                                    errors.extend(self.validate_minimum_and_maximum_offset_date(answer))

                            if answer['type'] in ['Number', 'Currency', 'Percentage']:
                                numeric_answer_ranges[answer.get('id')] = self._get_numeric_range_values(
                                    answer, numeric_answer_ranges)

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
        schema_metadata = schema['metadata']

        if schema['theme'] in ['default', 'northernireland']:
            if 'ru_name' not in schema_metadata:
                errors.append(self._error_message('Metadata - ru_name not specified in metadata field'))
            default_metadata.append('ru_name')

        # Find all words that precede any of:
        all_metadata = set(re.findall(r"((?<=metadata\[\')\w+"  # metadata['
                                      r'|(?<=metadata\.)\w+'  # metadata.
                                      r"|(?<=meta\': \')\w+)", str(schema)))  # meta': '

        # Checks if piped/routed metadata is defined in the schema
        for metadata in all_metadata:
            if metadata not in schema_metadata.keys():
                errors.append(self._error_message('Metadata - {} not specified in metadata field'.format(metadata)))

        # Checks if unused metadata is defined
        for metadata in schema_metadata.keys():
            if metadata not in all_metadata and metadata not in default_metadata:
                errors.append(self._error_message('Unused metadata defined in metadata field - {}'.format(metadata)))

        return errors

    def validate_calculated_ids_in_answers_to_calculate_exists(self, question):
        # Validates that any answer ids within the 'answer_to_group'
        # list are existing answers within the question

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

    def validate_schema_routing_rule_routes_to_valid_target(self, dict_list, goto_key, rule):
        errors = []

        if 'goto' in rule and goto_key in rule['goto'].keys():
            referenced_id = rule['goto'][goto_key]

            if not self._is_contained_in_list(dict_list, referenced_id):
                invalid_block_error = 'Routing rule routes to invalid {} [{}]'.format(goto_key, referenced_id)
                errors.append(self._error_message(invalid_block_error))
        return errors

    @staticmethod
    def validate_schema_routing_rule_dependent_on_valid_answer(rule, answer_ids_with_group_id, block_or_group):
        errors = []

        rule = rule.get('goto') or rule.get('repeat')
        if 'when' in rule:
            when_errors = Validator.validate_when_rule(rule['when'], answer_ids_with_group_id, block_or_group['id'])
            if when_errors:
                errors.append(when_errors)

        return errors

    @staticmethod
    def validate_repeat_when_rule_restricted(rule, answer_ids_with_group_id, group):
        errors = []

        if 'repeat' in rule and 'when' in rule['repeat']:
            whens = rule['repeat']['when']
            if len(whens) > 1:
                errors.append(Validator._error_message('The "when" clause in the repeat for {} has more than one condition'
                                                       .format(group['id'])))

            for when in whens:
                if 'id' not in when:
                    errors.append(Validator._error_message('The "when" clause in the repeat for {} must be based on "id"'
                                                           .format(group['id'])))
                elif when['id'] in answer_ids_with_group_id and answer_ids_with_group_id[when['id']]['group_id'] != group['id']:
                    errors.append(Validator._error_message('The answer id - {} in the id key of the "when" clause for {} is not in the same group'
                                                           .format(when['id'], group['id'])))

        return errors

    @staticmethod
    def validate_repeat_rule_restricted(rule, block):
        errors = []

        if 'repeat' in rule:
            errors.append(Validator._error_message('The block {} has a repeating routing rule'
                                                   .format(block['id'])))

        return errors

    def validate_calculated_summary_type(self, block, answers_with_parent_ids):
        answers_to_calculate = block['calculation']['answers_to_calculate']
        try:
            answer_types = [
                answers_with_parent_ids[answer_id]['answer']['type']
                for answer_id in answers_to_calculate
            ]
        except KeyError as e:
            return [self._error_message(
                "Invalid answer id {} in block {}'s answers_to_calculate".format(e, block['id']))]

        duplicates = set([answer for answer in answers_to_calculate if answers_to_calculate.count(answer) > 1])
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

    def validate_routing_on_answer_options(self, block, answer):
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

    @staticmethod
    def validate_when_rule(when_clause, answer_ids_with_group_id, referenced_id):
        # Validates any answer id in a when clause exists within the schema
        answer_reference_id_fields = ('id', 'answer_count')

        for when in when_clause:
            # either of the reference fields may be in use, however it will
            # never be the case that both are defined since this is handled by
            # the JSON schema check
            present_id_ref_keys = [x for x in answer_reference_id_fields if x in when]

            if not present_id_ref_keys:
                # No further validation required if there are no references to answers
                continue

            id_ref_key = present_id_ref_keys.pop()

            if when[id_ref_key] not in answer_ids_with_group_id:
                return Validator._error_message('The answer id - {} in the {} key of the "when" clause for {} does not exist'
                                                .format(when[id_ref_key], id_ref_key, referenced_id))

            if id_ref_key == 'answer_count':
                if when['condition'] in ('contains', 'not contains'):
                    return Validator._error_message('The condition "{}" is not valid for an answer_count based "when" clause'
                                                    .format(when['condition']))

    def validate_multiple_question_titles(self, question_titles, question_id, answer_ids):
        # Validates that the last title in a question titles object contains only a value key
        # Also validates that in any title the value key is always the first key
        errors = []

        last_title = question_titles[-1]
        if len(last_title) != 1 or 'value' not in last_title:
            errors.append(self._error_message('The last value must be the default value with no "when" clause for {}'
                                              .format(question_id)))

        for title in question_titles:
            if 'when' in title:
                when_errors = self.validate_when_rule(title['when'], answer_ids, question_id)
                if when_errors:
                    errors.append(when_errors)

        return errors

    def validate_date_range(self, question):
        # If period_limits object is present in the DateRange question
        # Validates that a date range does not have a negative period and
        # Days can not be used to define limits for yyyy-mm date ranges

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

    def validate_minimum_and_maximum_offset_date(self, answer):
        # Validates if a date answer has a minimum and maximum
        errors = []

        if 'value' in answer['minimum'] and 'value' in answer['maximum']:
            minimum_date = self._get_offset_date_value(answer['minimum'])
            maximum_date = self._get_offset_date_value(answer['maximum'])

            if minimum_date > maximum_date:
                errors.append(self._error_message('The minimum offset date is greater than the maximum offset date'))

        return errors

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
        special_keys = ['id']
        duplicate_errors = []

        for special_key in special_keys:
            unique_items = []

            for value in self._parse_values(json_to_validate, special_key):
                if value in unique_items:
                    duplicate_errors.append(
                        self._error_message('Duplicate {} found. value {}'.format(special_key, value)))
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

    @staticmethod
    def _is_contained_in_list(dict_list, key_id):
        for dict_to_check in dict_list:
            if dict_to_check['id'] == key_id:
                return True

        return False

    def _parse_values(self, schema_json, parsed_key):
        ignored_keys = ['titles', 'routing_rules', 'skip_conditions']

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

    def _get_offset_date_value(self, answer_min_or_max):
        if answer_min_or_max['value'] == 'now':
            value = datetime.utcnow().strftime('%Y-%m-%d')
        else:
            value = answer_min_or_max['value']

        if 'offset_by' in answer_min_or_max:
            offset = answer_min_or_max['offset_by']
            value = self._get_relative_date(value, offset)

        return value

    def _get_relative_date(self, date_string, offset_object):
        # Returns a relative date given an offset or period object
        return self.convert_to_datetime(date_string) + relativedelta(years=offset_object.get('years', 0),
                                                                     months=offset_object.get('months', 0),
                                                                     days=offset_object.get('days', 0))

    @staticmethod
    def convert_to_datetime(value):
        date_format = '%Y-%m'
        if value and re.match(r'\d{4}-\d{2}-\d{2}', value):
            date_format = '%Y-%m-%d'

        return datetime.strptime(value, date_format) if value else None

    @staticmethod
    def _get_answers_with_parent_ids(json_to_validate):
        answers = {}

        for section in json_to_validate.get('sections'):
            for group in section.get('groups'):
                for block in group.get('blocks'):
                    if block.get('questions'):
                        for question in block['questions']:
                            for answer in question.get('answers', []):
                                answers[answer['id']] = {
                                    'answer': answer,
                                    'block': block['id'],
                                    'group_id': group['id'],
                                    'section': section['id']
                                }

        return answers
