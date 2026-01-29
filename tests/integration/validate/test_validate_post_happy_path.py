import pytest
import os
import importlib
import pytest
from fastapi.testclient import TestClient

def test_valid_schema_post(client, mock_ajv_valid, valid_schema):

    response = client.post("/validate", json=valid_schema)
    assert response.status_code == 200
    assert response.json() == {}