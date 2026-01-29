import json
from pathlib import Path
import pytest
import os
import importlib
import pytest
from fastapi.testclient import TestClient

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

@pytest.fixture
def mock_ajv_valid(monkeypatch):
    """Mock the AJV validation endpoint to always return a valid response (no errors."""
    def mock_post(*args, **kwargs):
        return MockResponse({}) # no errors

    monkeypatch.setattr(api.requests, "post", mock_post)


@pytest.fixture
def valid_schema():
    # Hard relative from known project structure
    schema_path = Path("tests/schemas/valid/test_valid_skip_conditions.json").resolve()
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path) as f:
        return json.load(f)