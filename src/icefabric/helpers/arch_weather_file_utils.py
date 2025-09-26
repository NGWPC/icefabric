"""
Moduile interacting with archival weather files

Utilities for loading/supplying/interacting/virtualizing
archival weather files, mainly to interface with icechunk
"""

import os
from pathlib import Path

import fsspec
import pandas as pd
import rioxarray as rxr
import xarray as xr
from tqdm import tqdm
from virtualizarr import open_virtual_dataset

from icefabric.builds.icechunk_s3_module import S3Path
from icefabric.schemas.topobathy import FileType


def load_tiff_file(fp: str, attr_name: str) -> xr.Dataset | xr.DataArray | list[xr.Dataset]:
    """
    Loads a GEOTIFF

    Takes a local filepath to a TIFF and loads it into an Xarray
    Dataset object. Could also return a Dataarray or list of
    Datasets.

    Parameters
    ----------
    fp : str
        File path to the TIFF that will be returned as a dataset.
    attr_name : str
        Name of the attribute of interest. Ex: "elevation".
        Note: Not all rasters will be elevation in future.

    Returns
    -------
    xr.Dataset | xr.DataArray | list[xr.Dataset]
        The Xarray representation of the TIFF file.

    Raises
    ------
    FileNotFoundError
    """
    if os.path.exists(fp) is False:
        raise FileNotFoundError(f"Cannot find: {fp}")
    ds = rxr.open_rasterio(fp)
    ds = ds.to_dataset(name=attr_name)
    return ds


def get_archival_weather_files(
    loc: str | S3Path, file_type: FileType | None = None, manual_file_pattern: str | None = None
) -> list[str]:
    """
    Collect files from a directory

    Given a directory in either local or S3 storage, return all files of a specific type or
    matching a file pattern.

    Parameters
    ----------
    loc : str | S3Path
        Directory housing the files - could be a string for a local path, or an S3Path object
        for files on an S3 bucket
    file_type : FileType | None, optional
        The file type to be collected - NETCDF, TIF, etc. Must be given if no manual pattern is
        supplied. By default None
    manual_file_pattern : str | None, optional
        If supplied, will collect filepaths according to the file pattern instead of by
        filetype. Should be parsable by an fsspec.glob() call. By default None

    Returns
    -------
    list[str]
        A list of all retrieved filepaths associated with the directory, file type and/or
        manual file pattern.

    Raises
    ------
    ValueError
    """
    sort_prefix = ""
    if type(loc) is S3Path:
        sort_prefix = "s3://"
        fs = fsspec.filesystem("s3")
    else:
        loc = os.path.abspath(loc)
        fs = fsspec.implementations.local.LocalFileSystem()

    if manual_file_pattern:
        print(manual_file_pattern)
        files = fs.glob(f"{str(loc)}/{manual_file_pattern}")
    else:
        if not file_type:
            raise ValueError("Must supply a file_type argument if no manual_file_pattern is given")
        files = fs.glob(f"{str(loc)}/*{file_type.value}")
    files = sorted([f"{sort_prefix}{f}" for f in files])
    return files


def extract_dates_from_archival_files(
    file_paths: list[str] | list[Path], file_pattern: str, just_year: bool | None = False
) -> list[pd.DatetimeIndex] | list[int]:
    """
    Pull dates out of list of file names

    Extracts and returns a sorted list of datetimes corresponding to the provided
    list of filepaths.

    Parameters
    ----------
    file_paths: list[str]
        List of filepaths. File names should correspond to a datetime, and
        should contain the datetime embedded in the filename.
    file_pattern: str
        Matching pattern used to extract the datetime. Format should match the files,
        with an asterisk replacing the datetime section of the filename.
    just_year: bool | None, optional
        If supplied, will only extract year values in int form.

    Returns
    -------
    list[DatetimeIndex] | list[int]
        Sorted list of the DatetimeIndexes extracted from the filenames. Same
        length and ordering as the list of filepaths. Could also just be years
        as ints.
    """
    pre, post = file_pattern.split("*")[0:2]
    files = [fp.split("/")[-1] for fp in file_paths]
    dates = [f.replace(pre, "").replace(post, "") for f in files]
    if just_year:
        date_dims = [pd.date_range(d, periods=1).year for d in sorted(dates)]
    else:
        date_dims = [pd.date_range(d, periods=1) for d in sorted(dates)]
    return date_dims


def _virtualize_datasets(
    file_list: list[str], loadable_vars: list[str] | None = None, testing_file_quantity: int | None = None
) -> list[xr.Dataset]:
    """
    Virtualize archival weather files

    Takes a list of archival weather filepaths and converts each to a virtual dataset.
    NOTE: May take a very long time to process if the filelist is long or large.

    Parameters
    ----------
    file_list : list[str]
        List of archival weather filepaths, each of which will be converted to a virtual dataset.
    loadable_vars : list[str] | None, optional
        List of variables to open as lazy numpy/dask arrays instead of instances of
        ManifestArray. By default None.
    testing_file_quantity : int | None, optional
        Include if you want to test the virtualization with a subset of files.
        Only opens the number specified, starting with the first in the list. By default None

    Returns
    -------
    list[xr.Dataset]
        List of the virtualized datasets derived from the provided archival weather files.
    """
    if testing_file_quantity:
        file_list = file_list[:testing_file_quantity]
    v_datasets = []
    for i in tqdm(
        range(len(file_list)),
        desc="Opening files as virtual datasets.",
        unit="files",
        ncols=125,
        colour="#37B6BD",
    ):
        v_datasets.append(
            open_virtual_dataset(filepath=file_list[i], indexes={}, loadable_variables=loadable_vars)
        )
    return v_datasets


def add_time_dim_to_datasets(
    timeless_datasets: list[xr.Dataset],
    datetimes: list[pd.DatetimeIndex],
    just_year: bool | None = False,
    testing_file_quantity: int | None = None,
) -> list[xr.Dataset]:
    """
    Add time dimension to a collection of data

    Expands each entry in a list of virtualized datasets with a single time dimension

    Parameters
    ----------
    timeless_datasets : list[xr.Dataset]
        List of virtualized datasets missing time dimensions.
    datetimes : list[pd.DatetimeIndex]
        List of the DatetimeIndexes that will be added onto ```timeless_datasets```.
        Should be the same length and ordering.
    just_year: bool | None, optional
        Include if your datetimes list is only years in int format. Will add a 'year' dimension
        instead. By default False.
    testing_file_quantity : int | None, optional
        Include if you want to only add the time dimension to a subset of the virtualized datasets.
        Only opens the number specified, starting with the first in the list.
        NOTE: Make sure the length of ```timeless_datasets``` and ```datetimes``` are equal after
        accounting for this. By default None.

    Returns
    -------
    list[xr.Dataset]
        List of the virtualized datasets with newly added time dimensions.
    """
    if testing_file_quantity:
        datetimes = datetimes[:testing_file_quantity]
    v_datasets = [
        d.expand_dims(year=t) if just_year else d.expand_dims(time=t)
        for d, t in zip(timeless_datasets, datetimes, strict=False)
    ]
    return v_datasets


def virtualize_and_concat_archival_files_on_time(
    location: str | S3Path,
    file_date_pattern: str,
    file_type: FileType | None = None,
    manual_file_pattern: str | None = None,
    just_year: bool | None = False,
    loadable_vars: list[str] | None = None,
    testing_file_quantity: int | None = None,
) -> xr.Dataset:
    """
    Virtualize a collection of weather files and combine them

    Per a given local file directory or S3 bucket directory, collect every archival
    weather file (with time data only in the filename) and virtualize and concatenate
    the set on a time dimension. Produces a single virtualized dataset.

    Parameters
    ----------
    lcoation : str | S3Path
        Directory housing the files - could be a string for a local path, or an S3Path object
        for files on an S3 bucket
    file_date_pattern : str
        Matching pattern used to extract the datetime. Format should match the files,
        with an asterisk replacing the datetime section of the filename.
    file_type: FileType | None, optional
        The file type to be collected - NETCDF, TIF, etc. Must be given if no manual pattern is
        supplied. By default None
    manual_file_pattern : str | None, optional
        If supplied, will collect filepaths according to the file pattern instead of by
        filetype. Should be parsable by an fsspec.glob() call. By default None.
    just_year: bool | None, optional
        Include if your filenames only contain years. Will add a 'year' dimension
        instead when virtualizing. By default False.
    loadable_vars : list[str] | None, optional
        List of dataset variables to open as lazy numpy/dask arrays when virtualizing,
        instead of instances of ManifestArray. Leads to data duplication, but is necessary
        in some cases. By default None.
    testing_file_quantity : int | None, optional
        Include if you want to test the virtualization with a subset files.
        Only opens the number specified, starting with the first. Useful for virtualizing
        smaller groups of files when testing or debugging. By default None.

    Returns
    -------
    xr.Dataset
        The fully time-concatenated, virtualized dataset.
    """
    arch_files = get_archival_weather_files(
        loc=location, file_type=file_type, manual_file_pattern=manual_file_pattern
    )
    datetimes = extract_dates_from_archival_files(arch_files, file_date_pattern, just_year=just_year)
    timeless_datasets = _virtualize_datasets(arch_files, loadable_vars, testing_file_quantity)
    time_added_datasets = add_time_dim_to_datasets(
        timeless_datasets, datetimes, just_year, testing_file_quantity
    )
    concat_dim = "year" if just_year else "time"
    final_dataset = xr.concat(
        time_added_datasets, dim=concat_dim, coords="minimal", compat="override", combine_attrs="override"
    )
    return final_dataset
