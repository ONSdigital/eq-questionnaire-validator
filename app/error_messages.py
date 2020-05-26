DUMB_QUOTES_FOUND = "Found dumb quotes(s) in schema text"
DUPLICATE_ID_FOUND = "Duplicate id found"

NO_RADIO_FOR_PRIMARY_PERSON_LIST_COLLECTOR = (
    "The primary person list collector block does not contain a Radio answer type"
)
NON_EXISTENT_PRIMARY_PERSON_LIST_COLLECTOR_ANSWER_VALUE = (
    "The primary person list collector block has an "
    "add_or_edit_answer value that is not present in the answer values"
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
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MIN = (
    "The referenced answer cannot be used to set the minimum of answer"
)
ANSWER_REFERENCE_CANNOT_BE_USED_ON_MAX = (
    "The referenced answer cannot be used to set the maximum of answer"
)
QUESTIONNAIRE_MUST_CONTAIN_PAGE = (
    "Questionnaire must contain one of [Confirmation page, Summary page, Hub page]"
)
QUESTIONNAIRE_ONLY_ONE_PAGE = (
    "Questionnaire can only contain one of [Confirmation page, Summary page, Hub page]"
)
ADD_OR_EDIT_ANSWER_REFERENCE_NOT_IN_MAIN_BLOCK = (
    "add_or_edit_answer reference uses id not found in main block question"
)
MULTIPLE_LIST_COLLECTORS_FOR_DRIVING_QUESTION = (
    "ListCollectorDrivingQuestion for list cannot be used with multiple ListCollectors"
)
SUMMARY_HAS_NON_TEXTFIELD_ANSWER = (
    "Summary concatenation can only be used for TextField answer types"
)
REQUIRED_HUB_SECTION_UNDEFINED = (
    "Required defined section hub does not appear in schema"
)
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
