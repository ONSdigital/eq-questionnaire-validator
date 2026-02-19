import json
import os
import urllib.request
from pathlib import Path
from typing import Mapping
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


@pytest.fixture
def load_valid_schema():
    """Load the valid JSON schema for testing."""
    schema_path = Path(__file__).parents[1] / "schemas" / "valid" / "test_valid_skip_conditions.json"

    if not schema_path.exists():
        error_message = f"Valid schema file not found: {schema_path}\nCheck if the file exists and the path is correct."
        raise FileNotFoundError(error_message)

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
