from pyiceberg.catalog import load_catalog


def test_xs_endpoint(client):
    """Test: GET /v1/ras_xs/{mip_hucid or ble_hucid}/dsreachid={reach_id}?xstype={mip or ble} - all valid arguments"""
    catalog = load_catalog("glue", **{"type": "glue", "glue.region": "us-east-1"})
    mip_hucid_list = [tup[1] for tup in catalog.list_tables("mip_xs")]
    ble_hucid_list = [tup[1] for tup in catalog.list_tables("ble_xs")]

    for mip_hucid in mip_hucid_list[:5]:
        response = client.get(f"/v1/ras_xs/{mip_hucid}?xstype=mip")
        assert response.status_code == 200, "Incorrect response"

        reachid = list(set(catalog.load_table(f"mip_xs.{mip_hucid}").scan().to_pandas()["ds_reach_id"]))[0]
        response2 = client.get(f"/v1/ras_xs/{mip_hucid}/dsreachid={reachid}?xstype=mip")
        assert response2.status_code == 200, "Incorrect response"

    for ble_hucid in ble_hucid_list[:5]:
        response = client.get(f"/v1/ras_xs/{ble_hucid}?xstype=ble")
        assert response.status_code == 200, "Incorrect response"

        reachid = list(set(catalog.load_table(f"ble_xs.{ble_hucid}").scan().to_pandas()["ds_reach_id"]))[0]
        response2 = client.get(f"/v1/ras_xs/{ble_hucid}/dsreachid={reachid}?xstype=ble")
        assert response2.status_code == 200, "Incorrect response"


def test_xs_subset_endpoint__422(client):
    """Test: GET /v1/ras_xs/08020203?xstype=NA - fails validator"""
    response = client.get("/v1/ras_xs/08020203?xstype=NA")
    assert response.status_code == 422

    response2 = client.get("/v1/ras_xs/08020203/dsreachid=NA?xstype=NA")
    assert response2.status_code == 422
