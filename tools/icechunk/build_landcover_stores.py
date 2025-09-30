"""A file to build the landcover stores using Icechunk"""

import argparse
from pathlib import Path

import icechunk as ic
import xarray as xr
from tqdm import tqdm
from virtualizarr import open_virtual_dataset

from icefabric.helpers import (
    add_time_dim_to_datasets,
    extract_dates_from_archival_files,
)


def build_landcover_store(virtual_files: str, output_path) -> None:
    """Creates a landcover store based on the NLCD data

    Parameters
    ----------
    virtual_files : str
        The path to where the virtual files live
    output_path : _type_
        _description_
    """
    abs_path = Path(virtual_files).resolve()

    # Create virtual chunk container
    store_config = ic.local_filesystem_store(str(abs_path))
    container = ic.VirtualChunkContainer(f"file://{abs_path}", store_config)

    # Set up credentials
    credentials = ic.containers_credentials({f"file://{abs_path}": None})

    # Create config and add container
    config = ic.RepositoryConfig.default()
    config.set_virtual_chunk_container(container)

    # Create storage for the repo
    storage = ic.local_filesystem_storage(str(Path(output_path).resolve()))

    # Create/open repository with correct class name
    nlcd_repo = ic.Repository.open_or_create(
        storage=storage,
        config=config,
        authorize_virtual_chunk_access=credentials,
    )

    # Get Files
    files = sorted([str(f) for f in abs_path.glob("*")])
    datetimes = extract_dates_from_archival_files(files, "Annual_NLCD_LndCov_*_CU_C1V0.tif", just_year=True)

    # Virtualize Data
    datasets = []
    for i in tqdm(
        range(len(files)),
        desc="Opening files as Virtual Datasets",
        unit="files",
        ncols=125,
        colour="#37B6BD",
    ):
        datasets.append(
            open_virtual_dataset(
                filepath=files[i],
                indexes={},
            )
        )
    time_added_datasets = add_time_dim_to_datasets(datasets, datetimes, just_year=True)
    ds = xr.concat(
        time_added_datasets, dim="year", coords="minimal", compat="override", combine_attrs="override"
    )

    # Write to icechunk
    session = nlcd_repo.writable_session("main")
    store = session.store  # A zarr store
    ds.virtualize.to_icechunk(store)
    _ = session.commit("Initial Commit: Building landcover store")

    print("Successfully wrote to icechunk")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 endpoint")

    parser.add_argument(
        "virtual_files", type=str, help="The Path to the files we're virtualizing into icechunk"
    )
    parser.add_argument("output_path", type=str, help="The Path to where the repo should be created")

    args = parser.parse_args()
    build_landcover_store(args.virtual_files, args.output_path)
