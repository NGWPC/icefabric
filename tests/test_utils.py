import pytest
from pyiceberg.catalog import Catalog

from icefabric.hydrofabric import find_origin
from icefabric.schemas import IdType


@pytest.mark.unit
def test_find_origin(hydrofabric_catalog: Catalog):
    """Testing the find origin function"""
    network = hydrofabric_catalog.load_table("hydrofabric.network")
    with pytest.raises(ValueError, match="No origin found"):
        find_origin(
            network_table=network,
            identifier="non-existent-id-12345",
            id_type=IdType.HL_URI.value,
        )

    network = hydrofabric_catalog.load_table("hydrofabric.network")
    with pytest.raises(ValueError, match="No origin found"):
        find_origin(
            network_table=network,
            identifier="non-existent-id-12345",
            id_type=IdType.HL_URI.value,
        )
