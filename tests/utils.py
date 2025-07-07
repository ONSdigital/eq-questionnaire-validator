"""Utility functions for testing purposes."""

import os
from json import load


def _open_and_load_schema_file(file):
    with open(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), file), encoding="utf8",
    ) as json_file:
        return load(json_file)
