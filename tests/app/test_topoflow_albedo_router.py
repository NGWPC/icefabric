from icefabric.schemas.modules import AlbedoValues


def test_albedo_endpoint(client):
    """Test: GET /v2/modules/topoflow/albedo - all valid arguments"""
    for landcover, albedo in AlbedoValues.__members__.items():
        response = client.get(f"/v1/modules/topoflow/albedo?landcover={landcover}")
        assert response.status_code == 200
        assert response.text == str(albedo.value)


def test_albedo_endpoint__422(client):
    """Test: GET /v2/modules/topoflow/albedo - fails validator"""
    response = client.get("/v1/modules/topoflow/albedo?landcover=nope")
    assert response.status_code == 422
