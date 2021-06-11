import os


def pytest_generate_tests(metafunc):
    if "valid_schema_filename" in metafunc.fixturenames:
        valid_schema_filenames = find_all_json_files("tests/schemas/valid")
        metafunc.parametrize("valid_schema_filename", valid_schema_filenames)
    if "rule_schema_filename" in metafunc.fixturenames:
        rule_schema_filenames = find_all_json_files("tests/schemas/rules")
        metafunc.parametrize("rule_schema_filename", rule_schema_filenames)


def find_all_json_files(folder_name):
    return [
        os.path.join(folder, filename)
        for folder, _, files in os.walk(folder_name)
        for filename in files
        if filename.endswith(".json")
    ]
