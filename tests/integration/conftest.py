from io import BytesIO
import json
from pathlib import Path
from typing import Mapping
import pytest
import os
import urllib.request
import urllib.error
import pytest
from fastapi.testclient import TestClient
import urllib

os.environ.setdefault("AJV_VALIDATOR_URL", "http://mock-ajv-validator/validate")

import api 

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
        raise FileNotFoundError(
            f"Valid schema file not found: {schema_path}\n"
            f"Check if the file exists and the path is correct."
        )
    
    with open(schema_path) as f:
        return json.load(f)

@pytest.fixture
def mock_ajv_valid(monkeypatch):
    """Mock the AJV validation endpoint to always return a valid response (no errors)."""
    def mock_post(*args, **kwargs):
        return MockResponse({}) # no errors

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def mock_ajv_error(monkeypatch):

    def mock_post(*args, **kwargs):
        return MockResponse({
            "errors": [
                {"keyword": "required", "message": "Missing survey_id'"},
                {"keyword": "type", "message": "Invalid data type for validation"}
            ]
        }) 

    monkeypatch.setattr(api.requests, "post", mock_post)

@pytest.fixture
def mock_urlopen_valid(monkeypatch, valid_schema):
    json_bytes = json.dumps(valid_schema).encode('utf-8')
    
    def mock_urlopen(url):
        return BytesIO(json_bytes)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

@pytest.fixture
def mock_urlopen_not_found(monkeypatch):
    def mock_urlopen(url):
        hdrs: Mapping[str, str] = {}
        raise urllib.error.HTTPError(
            url=url,
            code=404,
            msg="Not Found",
            hdrs=hdrs, # type: ignore[arg-type]
            fp=None
        )

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

@pytest.fixture
def mock_urlopen_failure(monkeypatch):
    def mock_urlopen(url):
        raise urllib.error.URLError("Failed to reach the server")

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

