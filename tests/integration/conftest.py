from io import BytesIO
import json
from pathlib import Path
import pytest
import os
import urllib.request
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
