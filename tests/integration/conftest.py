import importlib
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


@pytest.fixture(scope="session")
def api_module():
    os.environ.setdefault("AJV_VALIDATOR_URL", "http://mock-ajv-validator/validate")

    import api

    importlib.reload(api)  # make sure env var is applied even if api imported earlier
    return api


@pytest.fixture
def client(api_module):
    return TestClient(api_module.app)


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
        raise FileNotFoundError(
            f"Valid schema file not found: {schema_path}\n" f"Check if the file exists and the path is correct."
        )

    with open(schema_path) as f:
        return json.load(f)


@pytest.fixture
def mock_ajv_valid(api_module, monkeypatch):
    """Mock the AJV validation endpoint to always return a valid response (no errors)."""

    def mock_post(*args, **kwargs):
        return MockResponse({})  # no errors

    monkeypatch.setattr(api_module.requests, "post", mock_post)


@pytest.fixture
def mock_ajv_down(api_module, monkeypatch):
    def mock_post(*args, **kwargs):
        raise RequestException("AJV unavailable")

    monkeypatch.setattr(api_module.requests, "post", mock_post)


@pytest.fixture
def mock_ajv_error(api_module, monkeypatch):
    def mock_post(*args, **kwargs):
        return MockResponse({"errors": [{"message": "schema invalid"}]})

    monkeypatch.setattr(api_module.requests, "post", mock_post, raising=True)


@pytest.fixture
def mock_urlopen_valid(monkeypatch, valid_schema):
    json_bytes = json.dumps(valid_schema).encode("utf-8")

    def mock_urlopen(url):
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
    def mock_urlopen(url):
        raise urllib.error.URLError("Failed to reach the server")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
