import json
import pytest
import os
import importlib
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

def test_valid_schema_post(client, mock_ajv_valid):

    schema_path = Path(__file__).parents[3] / "tests" / "schemas" / "valid" / "test_valid_skip_conditions.json"

    if not schema_path.exists():
        raise FileNotFoundError(f"Cannot find schema: {schema_path}")

    with open(schema_path) as f:
        payload = json.load(f)

    response = client.post("/validate", json=payload)
    assert response.status_code == 200
    assert response.json() == {}