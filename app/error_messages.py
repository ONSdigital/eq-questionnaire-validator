INVALID_WHEN_RULE_ANSWER_VALUE = "Answer value in when rule has an invalid value"
NON_EXISTENT_WHEN_KEY = 'The answer id in the key of the "when" clause does not exist'
DUMB_QUOTES_FOUND = "Found dumb quotes(s) in schema text"
DUPLICATE_ID_FOUND = "Duplicate id found"
NO_RADIO_FOR_LIST_COLLECTOR = (
    "The list collector block does not contain a Radio answer type"
)
NO_RADIO_FOR_LIST_COLLECTOR_REMOVE = (
    "The list collector remove block does not contain a Radio answer type"
)

NON_EXISTENT_LIST_COLLECTOR_ADD_ANSWER_VALUE = (
    "The list collector block has an add_answer_value that is not "
    "present in the answer values"
)
NON_EXISTENT_LIST_COLLECTOR_REMOVE_ANSWER_VALUE = "The list collector block has a remove_answer_value that is not present in the answer values"

NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR = (
    "The primary person list collector block does not contain a Radio answer type"
)
NON_EXISTENT_PRIMARY_PERSON_LIST_COLLECTOR_ANSWER_VALUE = (
    "The primary person list collector block has an "
    "add_or_edit_answer value that is not present in the answer values"
)
NON_UNIQUE_ANSWER_ID_FOR_LIST_COLLECTOR_ADD = (
    "Multiple list collectors populate a list using different "
    "answer_ids in the add block"
)
NON_UNIQUE_ANSWER_ID_FOR_PRIMARY_LIST_COLLECTOR_ADD_OR_EDIT = (
    "Multiple primary person list collectors "
    "populate a list using different answer ids in the add_or_edit block"
)
PLACEHOLDERS_DONT_MATCH_DEFINITIONS = "Placeholders don't match definitions."
FIRST_TRANSFORM_CONTAINS_PREVIOUS_TRANSFORM_REF = (
    "Can't reference `previous_transform` in a first transform"
)
NO_PREVIOUS_TRANSFORM_REF_IN_CHAIN = (
    "`previous_transform` not referenced in chained transform"
)
FOR_LIST_NEVER_POPULATED = "for_list is not populated by any ListCollector blocks"
METADATA_REFERENCE_INVALID = "Invalid metadata reference"
ANSWER_REFERENCE_INVALID = "Invalid answer reference"
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MIN = (
    "The referenced answer cannot be used to set the minimum of answer"
)
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MAX = (
    "The referenced answer cannot be used to set the maximum of answer"
)
ANSWER_SELF_REFERENCE = "Invalid answer reference (self-reference)"
ANSWER_LABEL_VALUE_MISMATCH = "Found mismatching answer value for label"
ANSWER_RANGE_INVALID = "Invalid range of min and max is possible for answer"
ANSWER_NOT_IN_QUESTION = "Answer does not exist within this question"
PERIOD_MIN_GREATER_THAN_MAX = "The minimum period is greater than the maximum period"
PERIOD_LIMIT_CANNOT_USE_DAYS = (
    "Days can not be used in period_limit for yyyy-mm date range"
)
PERIOD_LIMIT_CANNOT_USE_DAYS_MONTHS = (
    "Days/Months can not be used in period_limit for yyyy date range"
)
LIST_REFERENCE_INVALID = "Invalid list reference"
LIST_COLLECTOR_KEY_MISSING = "Missing key in ListCollector"
QUESTIONNAIRE_MUST_CONTAIN_PAGE = (
    "Questionnaire must contain one of [Confirmation page, Summary page, Hub page]"
)
QUESTIONNAIRE_ONLY_ONE_PAGE = (
    "Questionnaire can only contain one of [Confirmation page, Summary page, Hub page]"
)
RELATIONSHIP_COLLECTOR_HAS_INVALID_ANSWER_TYPE = (
    "Only answers of type Relationship are valid in RelationshipCollector blocks."
)
RELATIONSHIP_COLLECTOR_HAS_MULTIPLE_ANSWERS = (
    "RelationshipCollector contains more than one answer."
)
ADD_OR_EDIT_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK = (
    "add_or_edit_answer reference uses id not found in main block question"
)
ADD_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK = (
    "add_answer reference uses id not found in main block question"
)
REMOVE_ANSWER_REFERENCE_NOT_IN_REMOVE_BLOCK = (
    "remove_answer reference uses id not found in remove_block"
)
LIST_COLLECTOR_ADD_EDIT_IDS_DONT_MATCH = (
    "The list collector block contains an add block and edit block"
    " with different answer ids"
)
MULTIPLE_LIST_COLLECTORS_FOR_DRIVING_QUESTION = (
    "ListCollectorDrivingQuestion for list cannot be used with multiple ListCollectors"
)
NON_CHECKBOX_COMPARISON_ID = (
    "The comparison id is not of answer type `Checkbox`. The condition can only reference "
    "`Checkbox` answers when using `comparison id`"
)
NON_MATCHING_WHEN_ANSWER_AND_COMPARISON_TYPES = (
    "The answers used as comparison id and answer id in the `when` clause have "
    "different types"
)
FOUND_MISSING_METADATA = "Metadata not specified in metadata field"
FOUND_DUPLICATE_METADATA = "Metadata contains duplicates"
CHECKBOX_MUST_USE_CORRECT_CONDITION = (
    "The condition cannot be used with `Checkbox` answer type"
)
MULTIPLE_DRIVING_QUESTIONS_FOR_LIST = (
    "The block_id should be the only ListCollectorDrivingQuestion for list"
)
SUMMARY_HAS_NON_TEXTFIELD_ANSWER = (
    "Summary concatenation can only be used for TextField answer types"
)
ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_TYPE = (
    "All answers in block's answers_to_calculate must be of the same type"
)
ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_CURRENCY = (
    "All answers in block's answers_to_calculate must be of the same currency"
)
ANSWERS_TO_CALCULATE_MUST_HAVE_SAME_UNIT = (
    "All answers in block's answers_to_calculate must be of the same unit"
)
ANSWERS_TO_CALCULATE_HAS_INVALID_ID = (
    "Invalid answer id in block's answers_to_calculate"
)
ANSWERS_TO_CALCULATE_HAS_DUPLICATES = (
    "Duplicate answers in block's answers_to_calculate"
)
REQUIRED_HUB_SECTION_UNDEFINED = (
    "Required defined section hub does not appear in schema"
)

# QuestionValidator
MUTUALLY_EXCLUSIVE_CONTAINS_MANDATORY = (
    "MutuallyExclusive question type cannot contain mandatory answers."
)
NON_CHECKBOX_ANSWER = "Question is not of type Checkbox."

# AnswerValidator
DECIMAL_PLACES_UNDEFINED = "'decimal_places' must be defined and set to 2"
DECIMAL_PLACES_TOO_LONG = "Number of decimal places is greater than system limit"
INVALID_OFFSET_DATE = "The minimum offset date is greater than the maximum offset date"
INVALID_SUGGESTION_URL = "Suggestions url is invalid"
LIST_NAME_MISSING = "List name defined in action params does not exist"
BLOCK_ID_MISSING = "Block id defined in action params does not exist"
VALUE_MISMATCH = "Found mismatching answer value"
DEFAULT_ON_MANDATORY = "Default is being used with a mandatory answer"
MINIMUM_LESS_THAN_LIMIT = "Minimum value is less than system limit"
MAXIMUM_GREATER_THAN_LIMIT = "Maximum value is greater than system limit"
DUPLICATE_LABEL_FOUND = "Duplicate label found"
DUPLICATE_VALUE_FOUND = "Duplicate value found"
MINIMUM_CANNOT_BE_SET_WITH_ANSWER = (
    "The referenced answer cannot be used to set the minimum of answer"
)
MAXIMUM_CANNOT_BE_SET_WITH_ANSWER = (
    "The referenced answer cannot be used to set the maximum of answer"
)
GREATER_DECIMALS_ON_ANSWER_REFERENCE = (
    "The referenced answer has a greater number of decimal places than answer"
)

# Variants
VARIANTS_HAS_ONE_VARIANT = "Variants list only contains one variant"
VARIANTS_HAVE_DIFFERENT_ANSWER_LIST_LENGTHS = (
    "Variants in block contain different numbers of answers"
)
VARIANTS_HAVE_DIFFERENT_QUESTION_IDS = (
    "Variants contain more than one question_id for block"
)
VARIANTS_HAVE_DIFFERENT_DEFAULT_ANSWERS = (
    "Variants contain different default answers for block"
)
VARIANTS_HAVE_MISMATCHED_ANSWER_IDS = "Variants have mismatched answer_ids for block"
VARIANTS_HAVE_MISMATCHED_ANSWER_TYPES = (
    "Variants have mismatched answer types for block"
)
VARIANTS_HAVE_MULTIPLE_QUESTION_TYPES = (
    "Variants have more than one question type for block."
)

# Routing
ROUTE_TARGET_INVALID = "Routing rule routes to invalid"
ROUTE_MUST_CONTAIN_DEFAULT = (
    "The routing rules for group or block must contain a default routing rule without a "
    "when rule"
)
ROUTE_HAS_TOO_MANY_DEFAULTS = "The routing rules for group or block cannot contain multiple default routing rules."
# AnswerRouting
UNDEFINED_QUESTION_DEFAULT_ROUTE = "Default route not defined for optional question"
UNDEFINED_ANSWER_ROUTING_RULE = "Routing rule not defined for answer missing options"
CHECKBOX_CONDITION_ONLY = "This condition can only be used with `Checkbox` answer types"
