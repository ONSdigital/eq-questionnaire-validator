import os


def pytest_generate_tests(metafunc):
    if "valid_schema_filename" in metafunc.fixturenames:
        valid_schema_filenames = all_valid_schema_files()
        metafunc.parametrize("valid_schema_filename", valid_schema_filenames)


def all_valid_schema_files():
    schema_files = []
    for folder, _, files in os.walk("tests/schemas/valid"):
        for filename in files:
            if filename.endswith(".json") and "invalid" not in filename:
                schema_files.append(os.path.join(folder, filename))
    return schema_files
