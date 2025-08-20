"""A simple script to convert the v2.2 hydrofabric to parquet"""

import argparse
import re
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import httpx
import numpy as np
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
RFC
---
>>> xr.open_dataset("/Users/taddbindas/projects/NGWPC/icefabric/data/2023-04-01_00.60min.BCRT2.RFCTimeSeries.ncdf")
<python-input-1>:1: FutureWarning: In a future version, xarray will not decode timedelta values based on the presence of a timedelta-like units attribute by default. Instead it will rely on the presence of a timedelta64 dtype attribute, which is now xarray's default way of encoding timedelta64 values. To continue decoding timedeltas based on the presence of a timedelta-like units attribute, users will need to explicitly opt-in by passing True or CFTimedeltaCoder(decode_via_units=True) to decode_timedelta. To silence this warning, set decode_timedelta to True, False, or a 'CFTimedeltaCoder' instance.
  xr.open_dataset("/Users/taddbindas/projects/NGWPC/icefabric/data/2023-04-01_00.60min.BCRT2.RFCTimeSeries.ncdf")
<xarray.Dataset> Size: 1kB
Dimensions:              (nseries: 1, forecastInd: 289)
Dimensions without coordinates: nseries, forecastInd
Data variables:
    stationId            |S5 5B ...
    issueTimeUTC         (nseries) |S19 19B ...
    discharges           (nseries, forecastInd) float32 1kB ...
    synthetic_values     (nseries, forecastInd) int8 289B ...
    totalCounts          (nseries) int16 2B ...
    observedCounts       (nseries) int16 2B ...
    forecastCounts       (nseries) int16 2B ...
    timeSteps            (nseries) timedelta64[ns] 8B ...
    discharge_qualities  (nseries) int16 2B ...
    queryTime            (nseries) datetime64[ns] 8B ...
Attributes:
    fileUpdateTimeUTC:           2023-04-03_00:42:00
    sliceStartTimeUTC:           2023-03-30_00:00:00
    sliceTimeResolutionMinutes:  60
    missingValue:                -999.99
    newest_forecast:             0
    NWM_version_number:          v2.1

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
        end_date = df_indexed.index.max().normalize() + pd.Timedelta(days=2)  # gets YYYY-MM-DD 00:00:00
        hourly_index = pd.date_range(start=start_date, end=end_date, freq="h")[
            :-1
        ]  # Remove the final timestamp to end at 23:00

        # Reindex with nearest interpolation
        df_extended = df_indexed.reindex(hourly_index, method="nearest")
        df = df_extended.reset_index()
    else:
        raise ValueError(f"Cannot interpolate non-daily values. Timestep is: {timestep}")
    stationId = xr.DataArray(
        data=location_id.encode("utf-8"),  # Convert to bytes like |S5
        dims=[],
        attrs={"long_name": info, "units": "-"},
    )
    discharges = xr.DataArray(
        data=df["Result"].values.reshape(1, -1)
        * 0.0283168,  # Reshape to (nseries, forecastInd). Convert to cms
        dims=["nseries", "forecastInd"],
        name="discharges",
        attrs={
            "long_name": "Obsverved and forecasted discharges. There are 48 hours of observed values before issue time (T0), that is the start time is T0 - 48 hours. Values after T0 (including T0) are forecasts that genenrally extend to 10 days, that is T0 + 240 hours. The total length of dischargs is 12 days in general except in cases where forecasts or observations that are longer than 10 days or 2 days respectively are available.",
            "units": "m^3/s",
        },
    )
    timeSteps = xr.DataArray(
        data=[pd.Timedelta(hours=1).value],  # This gives nanoseconds
        dims=["nseries"],
        name="timeSteps",
        attrs={"long_name": "Frequency/temporal resolution of forecast values"},
    )
    discharge_quality = xr.DataArray(
        data=[100],
        dims=["nseries"],
        attrs={
            "long_name": "Discharge quality 0 to 100 to be scaled by 100.",
            "units": "-",
            "multfactor": 0.01,
        },
    )
    queryTime = xr.DataArray(data=[np.datetime64("now", "ns")], dims=["nseries"])
    # Create the dataset
    ds = xr.Dataset(
        data_vars={
            "stationId": stationId,
            "discharges": discharges,
            "timeSteps": timeSteps,
            "discharge_quality": discharge_quality,
            "queryTime": queryTime,
        },
        attrs={
            "fileUpdateTimeUTC": pd.Timestamp("now").strftime("%Y-%m-%d_%H:%M:%S"),
            "sliceStartTimeUTC": pd.Timestamp(start_date).strftime("%Y-%m-%d_%H:%M:%S"),  # Use start_date
            "sliceTimeResolutionMinutes": 60,
            "usbr_catalog_item_id": params["itemId"],
        },
    )
    ds.to_netcdf(output_folder / f"{params['filename']}.nc")


def create_filename_from_item_title(item_title: str, start_date: str, end_date: str) -> str:
    """Create a clean filename from item title and dates."""
    clean_title = re.sub(r'[/\\:*?"<>|]', "_", item_title)
    clean_title = re.sub(r"\s+", " ", clean_title)  # Multiple spaces to single
    clean_title = clean_title.replace(" - ", "_").replace(" ", "_")
    clean_title = re.sub(r"_+", "_", clean_title)  # Multiple underscores to single
    clean_title = clean_title.strip("_")
    clean_title = clean_title.replace("_Time_Series_Data", "")
    clean_title = clean_title.replace("_Data", "")

    if len(clean_title) > 60:
        clean_title = clean_title[:60].rstrip("_")

    return f"{clean_title}_{start_date}_to_{end_date}"


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
                parameter_unit = attributes["parameterUnit"]
                if parameter_unit == "cfs":
                    valid_items.append(attributes["_id"])
                    info.append(attributes["itemTitle"])
            else:
                print(f"Error reading record: {item_response['status_code']}")
                raise ValueError
        except KeyError as e:
            msg = f"Cannot find data for item: {item}"
            print(msg)
            raise KeyError(msg) from e

    for item, _info in zip(valid_items, info, strict=True):
        file_name = create_filename_from_item_title(
            item_title=_info, start_date=start_date, end_date=end_date
        )
        # Build parameters
        params = {
            "type": "csv",
            "itemId": item,
            "before": end_date,
            "after": start_date,
            "filename": file_name,
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
        output_filename = output_folder / f"{params['filename']}.nc"
        print(f"Output file saved to: {output_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert USBR reservoir outflows into data to be used in RFC-DA"
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
        help="The start time for pulling streamflow outflows",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="The end time for pulling streamflow outflows",
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
