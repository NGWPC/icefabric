"""
Icechunk examples

General example/testing code for Icechunk functionality. Covers archival weather
file virtualization/concatenation & uploading/appending/retrieving data to/from repos.
"""

from dotenv import load_dotenv

import icefabric.helpers.nc_conv_utils as ncc_utils
from icefabric.builds import IcechunkRepo, S3Path
from icefabric.helpers import (
    get_archival_weather_files,
    load_tiff_file,
    virtualize_and_concat_archival_files_on_time,
)
from icefabric.schemas import FileType, NGWPCLocations

ICECHUNK_STORES = [loc for loc in NGWPCLocations if "_IC" in loc.name]
load_dotenv()


def output_icechunk_stores():
    """Print out each icechunk store"""
    for loc in ICECHUNK_STORES:
        print(f"{loc.name}\n    {loc.path}")


def snodas_virtualize_push_test(
    new_ic_repo: S3Path, test_quant: int | None = None, clean_up: bool | None = False
):
    """
    Push a collection of SNODAS NETCDFs

    Take the collection of SNODAS NETCDF files, virtualize and concatenate
    them, and create a new IC repo to store the combined dataset.

    Specify clean-up to delete the icechunk repo after creation.

    NOTE: Take care to not overwrite an existing IC repo
    """
    snodas_repo = IcechunkRepo(
        location=new_ic_repo, virtual_chunk_mapping=[{"bucket": "ngwpc-forcing", "region": "us-east-1"}]
    )
    nc_virt_ds = virtualize_and_concat_archival_files_on_time(
        location=NGWPCLocations.SNODAS_REF.path,
        file_date_pattern="zz_ssmv11034tS__T0001TTNATS*05HP001.nc",
        file_type=FileType.NETCDF,
        loadable_vars=["crs"],
        testing_file_quantity=test_quant,
    )
    snodas_repo.write_dataset(ds=nc_virt_ds, virtualized=True, commit="first commit")
    print(snodas_repo.retrieve_dataset())
    if clean_up:
        snodas_repo.delete_repo(quiet=True)


def snodas_yearly_virt_append_test(
    new_ic_repo: S3Path, years: range, test_quant: int | None = None, clean_up: bool | None = False
):
    """
    Incrementally push a by-year-collection of SNODAS NETCDFs

    Take the collection of SNODAS NETCDF files and virtualize/concatenate
    them on a yearly basis. The year range is supplied. The data is virtualized
    and concatted individually by year, and each year is appended to the IC repo.

    Specify clean-up to delete the icechunk repo after creation.

    NOTE: Take care to not overwrite an existing IC repo
    """
    snodas_repo = IcechunkRepo(
        location=new_ic_repo, virtual_chunk_mapping=[{"bucket": "ngwpc-forcing", "region": "us-east-1"}]
    )
    for y in years:
        nc_virt_ds = virtualize_and_concat_archival_files_on_time(
            location=NGWPCLocations.SNODAS_REF.path,
            file_date_pattern="zz_ssmv11034tS__T0001TTNATS*05HP001.nc",
            manual_file_pattern=f"zz_ssmv11034tS__T0001TTNATS{y}*.nc",
            file_type=FileType.NETCDF,
            loadable_vars=["crs"],
            testing_file_quantity=test_quant,
        )
        if y == min(years):
            snodas_repo.write_dataset(ds=nc_virt_ds, virtualized=True, commit="first commit")
        else:
            snodas_repo.append_virt_data_to_store(
                vds=nc_virt_ds, append_dim="time", commit=f"appended new data from the year {y}"
            )
        del nc_virt_ds
    print(snodas_repo.retrieve_dataset())
    if clean_up:
        snodas_repo.delete_repo(quiet=True)


def land_cover_virtualize_push_test(
    new_ic_repo: S3Path, test_quant: int | None = None, clean_up: bool | None = False
):
    """
    Push a collection of NLCD GEOTIFFs

    Take the collection of NLCD GEOTIFF files, virtualize and concatenate
    them, and create a new IC repo to store the combined dataset.

    Specify clean-up to delete the icechunk repo after creation.

    NOTE: Take care to not overwrite an existing IC repo
    """
    nlcd_repo = IcechunkRepo(
        location=new_ic_repo, virtual_chunk_mapping=[{"bucket": "ngwpc-hydrofabric", "region": "us-east-1"}]
    )
    nlcd_vrt_ds = virtualize_and_concat_archival_files_on_time(
        location=NGWPCLocations.NLCD_REF.path,
        file_date_pattern="Annual_NLCD_LndCov_*_CU_C1V0.tif",
        file_type=FileType.GEOTIFF,
        just_year=True,
        testing_file_quantity=test_quant,
    )
    nlcd_repo.write_dataset(ds=nlcd_vrt_ds, virtualized=True, commit="first commit")
    print(nlcd_repo.retrieve_dataset())
    if clean_up:
        nlcd_repo.delete_repo(quiet=True)


def topo_push_test(tiff_fp: str, attr_name: str, new_ic_repo: S3Path, clean_up: bool | None = False):
    """
    Push a topobathy GEOTIFF

    Take a topobathy GEOTIFF file and create a new IC repo
    containing that file's contents. 'repo_dir' specifies
    the IC repo name under the base topobathy S3 path

    Specify clean-up to delete the icechunk repo after creation.

    NOTE: Take care to not overwrite an existing IC repo
    """
    topo_repo = IcechunkRepo(location=new_ic_repo)
    topo_ds = load_tiff_file(tiff_fp, attr_name)
    topo_repo.write_dataset(ds=topo_ds, commit="first commit")
    print(topo_repo.retrieve_dataset())
    if clean_up:
        topo_repo.delete_repo(quiet=True)


def get_nc_by_year(years: range):
    """Return all SNODAS reference files for a given year range"""
    files = []
    for y in years:
        print(y)
        files += get_archival_weather_files(
            loc=NGWPCLocations.SNODAS_REF.path,
            file_type=FileType.NETCDF,
            manual_file_pattern=f"zz_ssmv11034tS__T0001TTNATS{y}*.nc",
        )
    return files


def conv_nc_by_year(year: str, test_quant: int | None = None):
    """Convert original NETCDF3 SNODAS files into NETCDF4."""
    ncc_utils.convert_nc_files_from_s3(
        orig=NGWPCLocations.SNODAS_V3.path,
        dest=NGWPCLocations.SNODAS_REF.path,
        manual_file_pattern=f"zz_ssmv11034tS__T0001TTNATS{year}*.nc",
        testing_file_quantity=test_quant,
    )


if __name__ == "__main__":
    snodas_virtualize_push_test(
        new_ic_repo=S3Path("hydrofabric-data", "ic_testing/snodas_test"), test_quant=5, clean_up=True
    )
    snodas_yearly_virt_append_test(
        new_ic_repo=S3Path("hydrofabric-data", "ic_testing/snodas_yearly_append_test"),
        years=range(2012, 2016),
        test_quant=3,
        clean_up=True,
    )
    land_cover_virtualize_push_test(
        new_ic_repo=S3Path("hydrofabric-data", "ic_testing/nlcd_test"), test_quant=5, clean_up=True
    )
