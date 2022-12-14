DUMB_QUOTES_FOUND = "Found dumb quotes(s) in schema text"
DUPLICATE_ID_FOUND = "Duplicate id found"
FOR_LIST_NEVER_POPULATED = "for_list is not populated by any ListCollector blocks"
MULTIPLE_LIST_COLLECTORS = "Section cannot contain multiple ListCollector blocks with a summary showing non-item answers"
RELATED_ANSWERS_NOT_IN_LIST_COLLECTOR = (
    "Related_answers id not present in any list collector"
)
NO_LABEL_FOR_RELATED_ANSWER = "No label found for answer '{answer_id}', only answers that support labels can be used as related answers"
ITEM_ANCHOR_ANSWER_ID_NOT_IN_LIST_COLLECTOR = "Item anchor answer id '{answer_id}' not present in any list collector for list name '{list_name}'"
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MIN = (
    "The referenced answer cannot be used to set the minimum of answer"
)
ANSWER_TYPE_FOR_OPTION_LABEL_FROM_VALUE_INVALID = "The answer type for option label from value is not of type ['Radio','Checkbox','Dropdown']"
ANSWER_TYPE_FOR_TRANSFORM_TYPE_INVALID = "Expected the answer type for '{transform}' transform to be type '{expected_type}' but got type '{answer_type}'"
ANSWER_UNIT_AND_TRANSFORM_UNIT_MISMATCH = "The answer unit and transform unit mismatch, '{answer_unit}' not '{transform_unit}'"
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MAX = (
    "The referenced answer cannot be used to set the maximum of answer"
)
UNSUPPORTED_QUESTION_SUMMARY_ANSWER_TYPE = (
    "Unsupported answer type used for question summary concatenation"
)
REQUIRED_HUB_SECTION_UNDEFINED = "Required section for hub is undefined"
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
