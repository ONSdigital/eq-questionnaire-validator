TYPE_STRING = "string"
TYPE_NUMBER = "number"
TYPE_ARRAY = "array"
TYPE_OBJECT = "object"
TYPE_DATE = "date"
TYPE_BOOLEAN = "boolean"
TYPE_NULL = "null"

ANSWER_TYPE_TO_JSON_TYPE = {
    "Address": TYPE_OBJECT,
    "Duration": TYPE_OBJECT,
    "Relationship": TYPE_OBJECT,
    "Checkbox": TYPE_ARRAY,
    "Date": TYPE_STRING,
    "MonthYearDate": TYPE_STRING,
    "YearDate": TYPE_STRING,
    "Dropdown": TYPE_STRING,
    "MobileNumber": TYPE_STRING,
    "Radio": TYPE_STRING,
    "TextArea": TYPE_STRING,
    "TextField": TYPE_STRING,
    "Currency": TYPE_NUMBER,
    "Number": TYPE_NUMBER,
    "Percentage": TYPE_NUMBER,
    "Unit": TYPE_NUMBER,
}

LIST_SELECTOR_TO_JSON_TYPE = {
    "count": TYPE_NUMBER,
    "first": TYPE_STRING,
    "primary_person": TYPE_STRING,
    "same_name_items": TYPE_ARRAY,
}

PYTHON_TYPE_TO_JSON_TYPE = {
    "dict": TYPE_OBJECT,
    "list": TYPE_ARRAY,
    "str": TYPE_STRING,
    "int": TYPE_NUMBER,
    "float": TYPE_NUMBER,
    "bool": TYPE_BOOLEAN,
    "NoneType": TYPE_NULL,
}

METADATA_TYPE_TO_JSON_TYPE = {
    "string": TYPE_STRING,
    "date": TYPE_STRING,
    "boolean": TYPE_BOOLEAN,
}


def resolve_answer_source_json_type(value_source, schema):
    answer_id = value_source["identifier"]
    answer_type = schema.answers_with_context[answer_id]["answer"]["type"]
    return ANSWER_TYPE_TO_JSON_TYPE[answer_type]


def resolve_calculated_summary_source_json_type(value_source, schema):
    block = schema.get_block(value_source["identifier"])
    if block["calculation"].get("answers_to_calculate"):
        answer_id = block["calculation"]["answers_to_calculate"][0]
    else:
        answer_value_source = block["calculation"]["operation"]["+"][0]
        answer_id = answer_value_source["identifier"]
    answer_type = schema.answers_with_context[answer_id]["answer"]["type"]
    return ANSWER_TYPE_TO_JSON_TYPE[answer_type]


def resolve_grand_calculated_summary_source_json_type(value_source, schema):
    block = schema.get_block(value_source["identifier"])
    first_calculated_summary_source = block["calculation"]["operation"]["+"][0]
    return resolve_value_source_json_type(first_calculated_summary_source, schema)


def resolve_metadata_source_json_type(value_source, schema):
    if metadata_id := value_source.get("identifier"):
        if metadata := schema.schema.get("metadata"):
            for values in metadata:
                if values.get("name") == metadata_id:
                    return METADATA_TYPE_TO_JSON_TYPE[values.get("type")]
    return TYPE_STRING


def resolve_list_source_json_type(value_source):
    if selector := value_source.get("selector"):
        return LIST_SELECTOR_TO_JSON_TYPE[selector]
    return TYPE_ARRAY


def resolve_value_source_json_type(value_source, schema):
    source = value_source["source"]
    if source == "answers":
        return resolve_answer_source_json_type(value_source, schema)

    if source == "calculated_summary":
        return resolve_calculated_summary_source_json_type(value_source, schema)

    if source == "grand_calculated_summary":
        return resolve_grand_calculated_summary_source_json_type(value_source, schema)

    if source == "metadata":
        return resolve_metadata_source_json_type(value_source, schema)

    if source == "list":
        return resolve_list_source_json_type(value_source)

    return TYPE_STRING


def python_type_to_json_type(python_type):
    return PYTHON_TYPE_TO_JSON_TYPE[python_type]
