import json
import os
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient
from requests import RequestException

import api

os.environ.setdefault("AJV_VALIDATOR_URL", "http://mock-ajv-validator/validate")


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(api.app)


class MockResponse:
    """Mock response for testing."""

    def __init__(self, json_data: dict):
        self.json_data = json_data

    def json(self) -> dict:
        return self.json_data


def _load_schema(schema_path: Path):
    with open(schema_path, encoding="utf-8") as schema_file:
        return json.load(schema_file)


@pytest.fixture
def load_valid_schema():
    """Return a known-valid questionnaire schema used by integration tests."""
    valid_path = Path("tests/schemas/valid/test_valid_skip_conditions.json")
    return _load_schema(valid_path)


@pytest.fixture
def load_invalid_schema():
    """Return an invalid questionnaire schema used by integration tests."""
    invalid_path = Path("tests/schemas/invalid/test_invalid_relationship_list_doesnt_exist.json")
    return _load_schema(invalid_path)


@pytest.fixture
def mock_ajv_valid(monkeypatch):
    """Mock the AJV validation endpoint to always return a valid response (no errors)."""

    def mock_post(*_args, **_kwargs):
        return MockResponse({})  # no errors

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def mock_ajv_down(monkeypatch):
    """Mock the AJV validation endpoint to simulate a down service."""

    def mock_post(*_args, **_kwargs):
        error_message = "AJV unavailable"
        raise RequestException(error_message)

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def mock_urlopen_not_found(monkeypatch):
    """Mock the urlopen function to simulate a 404 Not Found error."""

    def mock_urlopen(url):
        headers: Mapping[str, str] = {}
        raise HTTPError(url=url, code=404, msg="Not Found", hdrs=headers, fp=None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)


@pytest.fixture
def mock_urlopen_failure(monkeypatch):
    """Mock the urlopen function to simulate a failure."""

    def mock_urlopen(_url):
        error_message = "Failed to reach the server"
        raise URLError(error_message)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)
