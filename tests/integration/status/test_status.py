def test_status_endpoint(client):
    response = client.get("/status")
    assert response.status_code == 200