import pytest
import xarray as xr

from icefabric.builds import IcechunkRepo
from icefabric.schemas import NGWPCTestLocations

ic_list = NGWPCTestLocations._member_names_
params = [pytest.param(getattr(NGWPCTestLocations, name), id=f"Icechunk {name}") for name in ic_list]


@pytest.mark.parametrize("ic", params)
def test_icechunk_repo(ic: NGWPCTestLocations) -> None:
    """Confirm icechunk repos are valid"""
    ic_repo = IcechunkRepo(location=ic.path)
    ic_data = ic_repo.retrieve_dataset()
    assert isinstance(ic_data, xr.core.dataset.Dataset)
