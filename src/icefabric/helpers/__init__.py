"""Helper functions designed to assist with managing data. Similar to util functions"""

from .arch_weather_file_utils import (
    add_time_dim_to_datasets,
    extract_dates_from_archival_files,
    get_archival_weather_files,
    load_tiff_file,
    virtualize_and_concat_archival_files_on_time,
)
from .creds import load_creds
from .geopackage import table_to_geopandas, to_geopandas
from .io import load_pyiceberg_config
from .nc_conv_utils import conv_nc, convert_files_to_netcdf4, convert_nc_files_from_s3
from .topobathy_ic_to_tif import convert_topobathy_to_tiff

__all__ = [
    "get_archival_weather_files",
    "load_tiff_file",
    "virtualize_and_concat_archival_files_on_time",
    "extract_dates_from_archival_files",
    "add_time_dim_to_datasets",
    "load_creds",
    "table_to_geopandas",
    "to_geopandas",
    "convert_files_to_netcdf4",
    "convert_nc_files_from_s3",
    "conv_nc",
    "convert_topobathy_to_tiff",
    "load_pyiceberg_config",
]
