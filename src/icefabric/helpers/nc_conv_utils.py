"""Utilities for converting NETCDF3 files into NETCDF4"""

import os
import subprocess

from netCDF4 import Dataset as NCDataset
from tqdm import tqdm

import icefabric.helpers.arch_weather_file_utils as awf_utils
from icefabric.builds.icechunk_s3_module import S3Path


def convert_files_to_netcdf4(
    files: list[str],
    new_dir: str | None = "",
    fn_prefix: str | None = "",
    fn_suffix: str | None = "",
):
    """
    Convert collection of NCDF3 files to v4

    Given a list of NETCDF3 files, convert them all to NETCDF4 and store them
    in a new directory. Pre/suffixes can be specified as well for the new file
    names. Will be stored alongside the old files, or in a sibling directory if
    a dir name is provided.

    Parameters
    ----------
    files : list[str]
        The list of NETCDF3 filepaths to be converted.
    new_dir : str | None, optional
        If provided, will store the newly converted files
        in a different directory. It will create the directory
        in the same relative path as all the files to be converted.
        By default ""
    fn_prefix : str | None, optional
        If provided, will prepend a prefix to the new file names. By default "".
    fn_suffix : str | None, optional
        If provided, will append a suffix to the new file names. By default "".
    """
    if not new_dir and not fn_prefix and not fn_suffix:
        fn_suffix = "_new"
    for f in files:
        dir_path, basename = os.path.split(f)
        basename, ext = os.path.splitext(basename)
        if not os.path.exists(os.path.join(dir_path, new_dir)):
            os.makedirs(os.path.join(dir_path, new_dir))
        dir_path = os.path.join(dir_path, new_dir)
        conv_nc(f, f"{dir_path}/{fn_prefix}{basename}{fn_suffix}{ext}")


def convert_nc_files_from_s3(
    orig: S3Path,
    dest: S3Path,
    manual_file_pattern: str | None = None,
    testing_file_quantity: int | None = None,
):
    """
    Convert NETCDF3 collection from S3 location to v4

    Given an S3 path populated with NETCDF3 files, sequentially
    DL & convert them to NETCDF4, then re-upload them to a different
    S3 path. All files created on local filesystems are deleted as the
    process runs.

    Parameters
    ----------
    orig : S3Path
        S3 path containing the files to be converted
    dest : S3Path
        S3 path where the newly-converetd files will be
        uploaded.
    manual_file_pattern : str | None, optional
        If given, will supply a manual file pattern to
        when gathering the filepaths for conversion. May be
        useful to only include subsets of files. By default None.
    testing_file_quantity : int | None, optional
        Include if you want to test the conversion with a subset files.
        Only opens the number specified, starting with the first. By default None.
    """
    temp_down_dir = os.path.join(os.getcwd(), ".tmp")
    temp_conv_dir = os.path.join(os.getcwd(), ".tmp/conv")
    nc3_file_list = awf_utils.get_archival_weather_files(
        loc=orig, file_type=awf_utils.FileType.NETCDF, manual_file_pattern=manual_file_pattern
    )
    if testing_file_quantity:
        nc3_file_list = nc3_file_list[:testing_file_quantity]
    os.makedirs(temp_down_dir, exist_ok=True)
    os.makedirs(temp_conv_dir, exist_ok=True)

    for i in tqdm(
        range(len(nc3_file_list)),
        desc="Converting netcdf files from S3",
        unit="files",
        ncols=125,
        colour="#37B6BD",
    ):
        nc3_file = nc3_file_list[i].removesuffix("s3://").split("/")[-1]
        down_path = os.path.join(temp_down_dir, nc3_file)
        conv_path = os.path.join(temp_conv_dir, "conv.nc")
        subprocess.call(["aws", "s3", "cp", nc3_file_list[i], down_path, "--quiet"])
        conv_nc(down_path, conv_path, quiet=True)
        subprocess.call(["aws", "s3", "cp", conv_path, f"{str(dest)}/{nc3_file}", "--quiet"])
        subprocess.call(["rm", down_path, "-f"])
        subprocess.call(["rm", conv_path, "-f"])


def conv_nc(orig_file_path: str, new_file_path: str, quiet: bool | None = False):
    """
    Given a NETCDF3-formatted file, convert it to NETCDF4.

    Parameters
    ----------
    orig_file_path : str
        NETCDF3 filepath.
    new_file_path : str
        Filepath where the converted file will end up.
    quiet : bool | None, optional
        Provide if no print/log statements are desired.
        By default False.
    """
    # Open the NetCDF3 file in read mode
    nc3_data = NCDataset(orig_file_path, mode="r", format="NETCDF3_CLASSIC")

    # Create a new NetCDF4 file in write mode
    nc4_data = NCDataset(new_file_path, mode="w", format="NETCDF4")

    # Copy global attributes
    for attr_name in nc3_data.ncattrs():
        nc4_data.setncattr(attr_name, nc3_data.getncattr(attr_name))

    # Copy dimensions
    for dim_name, dim in nc3_data.dimensions.items():
        nc4_data.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)

    # Copy variables
    for var_name, var in nc3_data.variables.items():
        nc4_var = nc4_data.createVariable(var_name, var.datatype, var.dimensions)
        nc4_var.setncatts({attr_name: var.getncattr(attr_name) for attr_name in var.ncattrs()})
        nc4_var[:] = var[:]

    # Close both files
    nc3_data.close()
    nc4_data.close()

    if not quiet:
        print(f"Conversion from NetCDF3 to NetCDF4 completed: {new_file_path}")
