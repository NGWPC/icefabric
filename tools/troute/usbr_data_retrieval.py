"""A simple script to convert the v2.2 hydrofabric to parquet"""

import argparse
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import xarray as xr

from icefabric.helpers import EXT_RISE_BASE_URL, RISE_HEADERS, make_sync_get_req_to_rise


def valid_date(s: str) -> datetime:
    """Validates a string input into a datetime

    Parameters
    ----------
    s : str
        the str datetime

    Returns
    -------
    datetime
        the output datetime in the correct format

    Raises
    ------
    ValueError
        Not a valid date
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError as e:
        msg = f"Not a valid date: '{s}'. Expected format: YYYY-MM-DD."
        raise ValueError(msg) from e


"""
USGS:
----
>>> xr.open_dataset("/Users/taddbindas/projects/NGWPC/icefabric/data/2023-04-01_00_00_00.15min.usgsTimeSlice.ncdf")
<xarray.Dataset> Size: 3kB
Dimensions:            (stationIdInd: 57)
Dimensions without coordinates: stationIdInd
Data variables:
    stationId          (stationIdInd) |S15 855B ...
    time               (stationIdInd) |S19 1kB ...
    discharge          (stationIdInd) float32 228B ...
    discharge_quality  (stationIdInd) int16 114B ...
    queryTime          (stationIdInd) datetime64[ns] 456B ...
Attributes:
    fileUpdateTimeUTC:           2023-04-01_04:54:15
    sliceCenterTimeUTC:          2023-04-01_00:00:00
    sliceTimeResolutionMinutes:  15

USACE
-----
>>> xr.open_dataset("/Users/taddbindas/projects/NGWPC/icefabric/data/2023-04-01_00_00_00.15min.usaceTimeSlice.ncdf", decode_times=False)
<xarray.Dataset> Size: 0B
Dimensions:            (stationIdInd: 0)
Dimensions without coordinates: stationIdInd
Data variables:
    stationId          (stationIdInd) |S15 0B ...
    time               (stationIdInd) |S19 0B ...
    discharge          (stationIdInd) float32 0B ...
    discharge_quality  (stationIdInd) int16 0B ...
    queryTime          (stationIdInd) int32 0B ...
Attributes:
    fileUpdateTimeUTC:           2023-04-01_04:55:00
    sliceCenterTimeUTC:          2023-04-01_00:00:00
    sliceTimeResolutionMinutes:  15
"""


def write_ds(df: pd.DataFrame, params: dict[str, Any], location_id: str, info: str, output_folder: Path):
    """Writes the newly obtained USBR data to disk in the T-Route specified format"""
    timestep = df["Timestep"].values[0]
    if timestep == "daily":
        df["Datetime (UTC)"] = pd.to_datetime(df["Datetime (UTC)"])
        df_indexed = df.set_index("Datetime (UTC)")

        # Creates an extended hourly range from 00:00 of first day to 00:00 of day after last day
        start_date = df_indexed.index.min().normalize()  # gets YYYY-MM-DD 00:00:00
        end_date = df_indexed.index.max().normalize() + pd.Timedelta(days=1)  # gets YYYY-MM-DD 00:00:00
        interpolated_index = pd.date_range(start=start_date, end=end_date, freq="15min")[
            :-1
        ]  # Remove the final timestamp to end at 23:00

        # Reindex with nearest interpolation
        df_extended = df_indexed.reindex(interpolated_index, method="nearest")
        df = df_extended.reset_index()
        df = df.rename(columns={"Datetime (UTC)": "Datetime (UTC)"})  # Ensure column name is preserved

        # Convert hourly to 15-minute intervals
        df["index"] = pd.to_datetime(df["index"])
        df_indexed = df.set_index("index")
    else:
        raise ValueError(f"Cannot interpolate non-daily values. Timestep is: {timestep}")

    # Create a separate file for each 15-minute timestamp
    for timestamp, row in df_indexed.iterrows():
        # Format timestamp for filename: YYYY-MM-DD_HH:MM:SS
        time_str = timestamp.strftime("%Y-%m-%d_%H:%M:%S")
        file_name = f"{time_str}.15min.usbrTimeSlice.ncdf"

        # Create arrays for this single timestamp
        stationId = xr.DataArray(
            data=[str(location_id).encode("utf-8")],  # Single station as array
            dims=["stationIdInd"],
            attrs={"long_name": info, "units": "-"},
        )

        time_array = xr.DataArray(
            data=[time_str.encode("utf-8")],  # Single timestamp as array
            dims=["stationIdInd"],
            attrs={"long_name": "YYYY-MM-DD_HH:mm:ss UTC", "units": "UTC"},
        )

        if row["Units"] == "cfs":
            row["Result"] = row["Result"] * 0.0283168
        discharge = xr.DataArray(
            data=[row["Result"]],  # Convert to cms, single value as array
            dims=["stationIdInd"],
            attrs={
                "long_name": "Discharge",
                "units": "m^3/s",
            },
        )

        discharge_quality = xr.DataArray(
            data=[1],  # Single quality value
            dims=["stationIdInd"],
            attrs={
                "long_name": "Discharge quality flag",
                "units": "-",
            },
        )

        queryTime = xr.DataArray(
            data=[int(pd.Timestamp.now().timestamp())],  # Unix timestamp as integer
            dims=["stationIdInd"],
            attrs={
                "long_name": "Query time as unix timestamp",
                "units": "seconds since 1970-01-01",
            },
        )

        # Create the dataset matching USGS TimeSlice format
        ds = xr.Dataset(
            data_vars={
                "stationId": stationId,
                "time": time_array,
                "discharge": discharge,
                "discharge_quality": discharge_quality,
                "queryTime": queryTime,
            },
            attrs={
                "fileUpdateTimeUTC": pd.Timestamp.now().strftime("%Y-%m-%d_%H:%M:%S"),
                "sliceCenterTimeUTC": time_str,
                "sliceTimeResolutionMinutes": 15,
                "usbr_catalog_item_id": params.get("itemId", ""),
            },
        )

        # Save individual file
        output_file = output_folder / file_name
        ds.to_netcdf(output_file)
        print(f"Created: {output_file}")


def result_to_file(location_id: str, start_date: str, end_date: str, output_folder: Path) -> None:
    """Calls the USBR API and formats the response for t-route

    Parameters
    ----------
    location_id : str
        the usbr reservoir ID
    output_folder : Path
        The path to the folder to dump the outputs
    """
    rise_response = make_sync_get_req_to_rise(f"{EXT_RISE_BASE_URL}/location/{location_id}")
    try:
        if rise_response["status_code"] == 200:
            relationships = rise_response["detail"]["data"]["relationships"]
            catalog_records = relationships["catalogRecords"]["data"]
        else:
            print(f"Error reading location: {rise_response['status_code']}")
            raise ValueError
    except KeyError as e:
        msg = f"Cannot find record for location_id: {location_id}"
        print(msg)
        raise KeyError(msg) from e

    all_catalog_items = []
    for record in catalog_records:
        try:
            record_id = record["id"].split("/rise/api/")[-1]
            record_response = make_sync_get_req_to_rise(f"{EXT_RISE_BASE_URL}/{record_id}")

            if record_response["status_code"] == 200:
                relationships = record_response["detail"]["data"]["relationships"]
                catalog_items = relationships["catalogItems"]["data"]
                all_catalog_items.extend(catalog_items)
            else:
                print(f"Error reading record: {record_response['status_code']}")
                raise ValueError
        except KeyError as e:
            msg = f"Cannot find item for record: {record}"
            print(msg)
            raise KeyError(msg) from e

    valid_items = []
    info = []
    for item in all_catalog_items:
        try:
            item_id = item["id"].split("/rise/api/")[-1]
            item_response = make_sync_get_req_to_rise(f"{EXT_RISE_BASE_URL}/{item_id}")
            if item_response["status_code"] == 200:
                attributes = item_response["detail"]["data"]["attributes"]
                parameter_group = attributes["parameterGroup"]
                parameter_unit = attributes["parameterUnit"]
                parameter_name = attributes["parameterName"]
                if (
                    parameter_group == "Lake/Reservoir Outflow"
                    and parameter_name == "Lake/Reservoir Release - Total"
                    and parameter_unit == "cfs"
                ):
                    # Currently only supporting reservoir releases in cfs
                    valid_items.append(attributes["_id"])
                    info.append(attributes["itemTitle"])
            else:
                print(f"Error reading record: {item_response['status_code']}")
                raise ValueError
        except KeyError as e:
            msg = f"Cannot find data for item: {item}"
            print(msg)
            raise KeyError(msg) from e

    # Asserts to ensure we only have one item found.
    assert len(valid_items) > 0, "Cannot find reservoir data. No releases found for location"
    assert len(valid_items) == 1, (
        "Cannot determine correct catalog id. Multiple entries. Please see development team"
    )

    item = valid_items[0]
    _info = info[0]
    # Build parameters
    params = {
        "type": "csv",
        "itemId": item,
        "before": end_date,
        "after": start_date,
        "order": "ASC",
    }

    # Build the URL
    base_url = f"{EXT_RISE_BASE_URL}/result/download"
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    download_url = f"{base_url}?{param_string}"

    # download the csv, write the xarray files
    response = httpx.get(download_url, headers=RISE_HEADERS, timeout=15).content
    csv_string = response.decode("utf-8")
    lines = csv_string.split("\n")
    start_row = None
    for i, line in enumerate(lines):
        if "#SERIES DATA#" in line:
            start_row = i + 1  # Use the row after "#SERIES DATA#" as the header
            break

    if start_row is not None:
        df = pd.read_csv(StringIO(csv_string), skiprows=start_row)
    else:
        raise NotImplementedError("Series Data not found. Throwing error.")
    write_ds(df, params, location_id=location_id, info=_info, output_folder=output_folder)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert USBR reservoir outflows into data to be used in the USBR Persistence"
    )

    parser.add_argument(
        "--location-id",
        type=str,
        required=True,
        help="The location ID to get pull streamflow from",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="The start time for pulling reservoir release data",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="The end time for pulling reservoir release data",
    )
    parser.add_argument(
        "--output-folder",
        type=Path,
        default=Path.cwd(),
        help="Output directory for parquet file (default is cwd)",
    )

    args = parser.parse_args()
    result_to_file(
        location_id=args.location_id,
        start_date=args.start_date,
        end_date=args.end_date,
        output_folder=args.output_folder,
    )
