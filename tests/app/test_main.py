import pytest


@pytest.mark.skip(reason="Does not work in OWP CI due to permissions but rest of API works")
def test_health_with_fixture(client):
    """Test using the client fixture from conftest.py."""
    response = client.head("/health")
    assert response.status_code == 200
