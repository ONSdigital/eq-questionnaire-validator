import json
import os
import urllib
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Mapping

import pytest
from fastapi.testclient import TestClient
from requests import RequestException

import api

os.environ.setdefault("AJV_VALIDATOR_URL", "http://mock-ajv-validator/validate")


@pytest.fixture
def client():
    return TestClient(api.app)


class MockResponse:
    def __init__(self, json_data: dict):
        self.json_data = json_data

    def json(self) -> dict:
        return self.json_data


@pytest.fixture(scope="session")
def valid_schema():
    # Adjust the path based on your structure
    # From tests/integration/conftest.py → go up to tests/ → then schemas/valid/
    schema_path = Path(__file__).parents[1] / "schemas" / "valid" / "test_valid_skip_conditions.json"

    if not schema_path.exists():
        error_msg = f"Valid schema file not found: {schema_path}\nCheck if the file exists and the path is correct."
        raise FileNotFoundError(error_msg)

    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_ajv_valid(monkeypatch):
    """Mock the AJV validation endpoint to always return a valid response (no errors)."""

    def mock_post(*_args, **_kwargs):
        return MockResponse({})  # no errors

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def mock_ajv_down(monkeypatch):
    def mock_post(*_args, **_kwargs):
        error_msg = "AJV unavailable"
        raise RequestException(error_msg)

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def mock_urlopen_valid(monkeypatch, test_valid_schema):
    json_bytes = json.dumps(test_valid_schema).encode("utf-8")

    def mock_urlopen(_url):
        return BytesIO(json_bytes)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)


@pytest.fixture
def mock_urlopen_not_found(monkeypatch):
    def mock_urlopen(url):
        hdrs: Mapping[str, str] = {}
        raise urllib.error.HTTPError(url=url, code=404, msg="Not Found", hdrs=hdrs, fp=None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)


@pytest.fixture
def mock_urlopen_failure(monkeypatch):
    def mock_urlopen(_url):
        error_msg = "Failed to reach the server"
        raise urllib.error.URLError(error_msg)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
