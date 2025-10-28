from itertools import product

import pytest

from app.routers.ras_xs.router import BoundingBox
from icefabric.schemas import XsType

xs_schema_types = [m.value for m in XsType]
good_ids = ["20059822", "17039777", "2539367"]
bad_ids = ["9920059822", "9917039777"]
bbox_good = [
    BoundingBox(min_lat=31.3323, min_lon=-109.0502, max_lat=37.0002, max_lon=-103.002),
    BoundingBox(min_lat=35.8, min_lon=-106.7, max_lat=37.0002, max_lon=-105.5),
    BoundingBox(min_lat=34.995, min_lon=-106.804, max_lat=35.232, max_lon=-106.463),
]
bbox_bad = [
    "min_lat=0&min_lon=0&max_lat=10&max_lon=10",
    "min_lat=37&min_lon=-109&max_lat=31&max_lon=-103",
    "min_lat=35&min_lon=-105&max_lat=37&max_lon=-106",
]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("id,schema", list(product(good_ids, xs_schema_types)))
async def test_get_xs_subset_gpkg_good(client, id, schema):
    response = client.get(f"/v1/ras_xs/{id}/?schema_type={schema}")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("id,schema", list(product(bad_ids, xs_schema_types)))
async def test_get_xs_subset_gpkg_bad(client, id, schema):
    response = client.get(f"/v1/ras_xs/{id}/?schema_type={schema}")
    assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("bbox,schema", list(product(bbox_good, xs_schema_types)))
async def test_get_by_geospatial_query_good(client, bbox, schema):
    response = client.get(f"/v1/ras_xs/within?schema_type={schema}&{str(bbox)}")
    assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("bbox,schema", list(product(bbox_bad, xs_schema_types)))
async def test_get_by_geospatial_query_bad(client, bbox, schema):
    response = client.get(f"/v1/ras_xs/within?schema_type={schema}&{str(bbox)}")
    assert response.status_code == 422
