def test_health_with_fixture(client):
    """Test using the client fixture from conftest.py."""
    response = client.head("/health")
    assert response.status_code == 200
