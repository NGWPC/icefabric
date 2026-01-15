import math
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import click
import dataretrieval.nwis as nwis
import numpy as np
import pandas as pd
import xarray as xr
from hydrotools.nwis_client.iv import IVDataService
from tqdm import tqdm

from icefabric.helpers import load_creds

load_creds()


# Mapping of gage types to their corresponding gage list files
GAGE_FILE_MAP = {
    "USGS": Path("tools/icechunk/streamflow_gages/USGS_gages.txt"),
    "ENVCA": Path("tools/icechunk/streamflow_gages/ENVCA_gages.txt"),
    "CADWR": Path("tools/icechunk/streamflow_gages/CADWR_gages.txt"),
    "TXDOT": Path("tools/icechunk/streamflow_gages/TXDOT_gages.txt"),
}


def get_usgs_streamflow(begin_date: str, end_date: str, site_info: str) -> pd.DataFrame:
    """Reads USGS Observational Streamflow from Hydrotools via IVDataService, processes it, and returns as dataframe"""
    site = site_info[0]
    service = IVDataService()

    begin_datetime = pd.to_datetime(begin_date)
    end_datetime = pd.to_datetime(end_date)
    hourly_timestamps = pd.date_range(start=begin_datetime, end=end_datetime, freq="h")

    # Creating a large array for all streamflow values. NaN values are for non-existent data
    aligned_gage_data = np.full((1, len(hourly_timestamps)), np.nan, dtype=np.float32)

    df = service.get(sites=site, startDT=begin_date, endDT=end_date)
    df = df[["value_time", "value"]]

    df["value"] = df["value"] * 0.0283168  # Convert from cfs to cms
    df = df.drop_duplicates(subset=["value_time"], keep="first").reset_index(drop=True)

    df = df.set_index("value_time")
    df = df.resample("h").first()

    common_indices = hourly_timestamps.isin(df.index)
    gauge_data_indices = np.where(common_indices)[0]
    if len(gauge_data_indices) > 0:
        # Only assigning values where timestamps match
        aligned_gage_data[0, gauge_data_indices] = df.loc[
            df.index.isin(hourly_timestamps[common_indices]), "value"
        ].values
    else:
        print(f"No observations found for {site}")

    sites_np = np.array([site], dtype=np.dtype("U16"))
    ds = xr.Dataset(
        {
            "q_cms": (
                ["id", "time"],
                aligned_gage_data,
                {
                    "long_name": "Streamflow",
                    "units": "cubic meters per second (m3/s)",
                    "description": "Observed streamflow from USGS gauge stations",
                    "source": "USGS National Water Information System",
                    "standard_name": "streamflow",
                    "coordinates": "id time",
                },
            )
        },
        coords={
            "id": (
                ["id"],
                sites_np,
                {
                    "long_name": "Gauge Station ID",
                    "description": "USGS gauge station identifier",
                },
            ),
            "time": (
                ["time"],
                hourly_timestamps,
                {"long_name": "Time", "standard_name": "time", "axis": "T"},
            ),
        },
        attrs={
            "title": "USGS Streamflow Observations",
            "history": f"Created {pd.Timestamp.now().strftime('%Y-%m-%d')}",
            "source": "USGS National Water Information System",
            "references": "https://waterdata.usgs.gov/nwis",
            "comment": "Hourly streamflow data resampled from USGS gauge measurements",
        },
    )

    df = ds.to_dataframe().reset_index().set_index(["time", "id"])
    return df


def get_cadwr_streamflow(begin_date: str, end_date: str, site_info: str) -> pd.DataFrame:
    """Pulls CADWR streamflow data from CADWR website, processes it, and returns as dataframe"""
    gage_id = site_info[0]
    sensor_num = site_info[1]
    dur_code = site_info[2]

    cadwr_url = f"https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={gage_id}&SensorNums={sensor_num}&dur_code={dur_code}&Start={begin_date}T00:00&End={end_date}T00:00"
    if gage_id == "MCD":
        # See comment below MCD's first call has to have an end time of 2005-11-17T11:00 to prevent retrieving
        # a bunch of junk data
        cadwr_url = f"https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={gage_id}&SensorNums={sensor_num}&dur_code={dur_code}&Start={begin_date}T00:00&End=2005-11-17T11:00"
    try:
        observations = pd.read_csv(cadwr_url)
        if gage_id == "MCD":
            # MCD was moved from a computed hourly value to a satellite sensed event. Because of this there
            # are two different datasets that need to be retrieved and appended to each other prior to
            # processing. This code block retrieves the second set of data and appends it to the first
            event_dur_code = "E"
            mcd_event_url = f"https://cdec.water.ca.gov/dynamicapp/req/CSVDataServlet?Stations={gage_id}&SensorNums={sensor_num}&dur_code={event_dur_code}&Start={begin_date}T00:00&End={end_date}T00:00"
            observations_mcd = pd.read_csv(mcd_event_url)
            if observations_mcd.empty:
                raise FileNotFoundError("No MCD event data found")
            observations = pd.concat([observations, observations_mcd])
    except FileNotFoundError as e:
        print(f"URL request failed for Gage - {gage_id}, General exception error = {e}")

    # Drop extra columns to be more efficient
    observations = observations[["OBS DATE", "VALUE"]]

    # Remove invalid values in data (BRT and ART signify discharge at stage below or above available
    # rating table and '___' for missing or unavailable sensor data
    # Convert columns to numeric, coercing non-numeric values to NaN
    observations["VALUE"] = pd.to_numeric(observations["VALUE"], errors="coerce")
    # Drop rows containing NaN in the 'salary' column
    observations.dropna(subset=["VALUE"], inplace=True)

    # convert from cfs to cms, to be consistent with simulations
    # observations.loc[:, 'VALUE'] *= math.pow(0.3048, 3)
    observations.loc[:, "VALUE"] = (observations["VALUE"].astype(float) * math.pow(0.3048, 3)).round(5)
    # Make value 5 sig-figs
    # observations.loc[:, 'VALUE'] = observations['VALUE'].round(5)
    # Check for duplicate time series, keep first by default
    observations = observations.drop_duplicates(subset=["OBS DATE"], keep="first").reset_index(drop=True)
    observations["OBS DATE"] = pd.to_datetime(observations["OBS DATE"], format="%Y%m%d %H%M")
    df = observations.rename(columns={"OBS DATE": "time", "VALUE": "q_cms"})

    # Resample to hourly, keep first measurement in each 1-hour bin
    df = df.set_index("time").resample("h").first()

    # Expand data to full date range
    full_date_range = pd.date_range(begin_date, end_date, freq="h")
    df = df.reindex(full_date_range)

    # Rename columns, add gage_id column then set multi-index
    df["id"] = gage_id
    df = df.reset_index(names="time").set_index(["time", "id"])

    return df


def get_txdot_streamflow(begin_date: str, end_date: str, site_info: str) -> pd.DataFrame:
    """Pulls TX DOT streamflow data using dataretrieval.nwis, processes it, and returns as dataframe"""
    gauge_id = site_info[0]
    col2chk = ["00060_rq-30", "00060_downstream, [rq-30", "00060", "00060_3"]
    df = nwis.get_record(sites=gauge_id, service="iv", start=begin_date, end=end_date, access="3")

    # Convert from cfs to cms & resample to hourly, keep first
    # measurement in each 1-hour bin
    print(f"Preprocessing TX DOT gauge {gauge_id} ...")
    if col2chk[0] in df.columns:
        df.loc[:, col2chk[0]] *= math.pow(0.3048, 3)
        df = df.resample("h").first()
        df = df[col2chk[0]]
        df = df.reset_index().rename(columns={"datetime": "time", col2chk[0]: "q_cms"})
    elif col2chk[1] in df.columns:
        df.loc[:, col2chk[1]] *= math.pow(0.3048, 3)
        df = df.resample("h").first()
        df = df[[col2chk[1]]]
        df = df.reset_index().rename(columns={"datetime": "time", col2chk[1]: "q_cms"})
    elif col2chk[2] in df.columns and col2chk[3] in df.columns:
        tqdm.write(f"Multiple discharge columns found for gage {gauge_id}")
        df.loc[:, col2chk[2]] *= math.pow(0.3048, 3)
        df.loc[:, col2chk[3]] *= math.pow(0.3048, 3)
        df = df.resample("h").first()
        df = df[[col2chk[2], col2chk[3]]]
        df = df.reset_index().rename(
            columns={"datetime": "time", col2chk[2]: "q_cms", col2chk[3]: "q_cms_denoted_3"}
        )

    df["time"] = df["time"].dt.tz_localize(None)
    full_date_range = pd.date_range(begin_date, end_date, freq="h")
    df = df.set_index("time").reindex(full_date_range)
    df["id"] = gauge_id
    df = df.reset_index(names="time").set_index(["time", "id"])

    return df


def get_envca_streamflow(begin_date: str, end_date: str, site_info: str, output_dir: Path) -> pd.DataFrame:
    """Downloads ENVCA streamflow data from S3 bucket, processes latest CSV, and returns as dataframe"""
    conus_root_path = "s3://ngwpc-hydrofabric/2.1/CONUS"
    gage_collection_dir = output_dir / "raw_s3_downloads"
    gage_collection_dir.mkdir(parents=True, exist_ok=True)
    gage_id = site_info[0]
    gage_type = site_info[2]
    command = [
        "aws",
        "s3",
        "cp",
        f"{conus_root_path}/{gage_id}",
        gage_collection_dir,
        "--recursive",
    ]
    subprocess.call(command)

    # Only getting latest CSV, converting to dataframe
    dates_dir = gage_collection_dir / f"OBSERVATIONAL/{gage_type}"
    dirs = [p.name for p in dates_dir.iterdir() if p.is_dir()]
    upload_dates = [datetime.strptime(d, "%Y_%B_%d_%H_%M_%S") for d in dirs]
    latest_dir = dirs[upload_dates.index(max(upload_dates))]
    downloaded_csv_path = dates_dir / latest_dir / f"{gage_id}_hourly_discharge.csv"
    df = pd.read_csv(downloaded_csv_path)

    # Expand date range, reformat and index along hourly time and gage id
    full_date_range = pd.date_range(begin_date, end_date, freq="h")
    df = df.rename(columns={"dateTime": "time"})
    df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%d %H:%M:%S")
    df = df.set_index("time").reindex(full_date_range)
    df["id"] = gage_id
    df = df.reset_index(names="time").set_index(["time", "id"])

    # Cleanup downloaded files
    shutil.rmtree(gage_collection_dir, ignore_errors=True)

    return df


@click.command()
@click.option(
    "--begin-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default="1979-01-01",
    help="Beginning of date range to download USGS streamflow data.",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default="2025-12-31",
    help="End of date range to download USGS streamflow data.",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("data/USGS_streamflow_parquets"),
    help="Local directory to save USGS hourly data as parquet files.",
)
@click.option(
    "--gage-type",
    type=click.Choice(list(GAGE_FILE_MAP.keys())),
    default="USGS",
    help="Which type of gage to download streamflow data for.",
)
@click.option(
    "--gage-list-file",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Path to text file containing list of USGS gage IDs to download. Overwrites mapped default gage list if provided.",
)
def download_usgs_streamflow(
    begin_date: str, end_date: str, output_dir: Path, gage_type: str, gage_list_file: Path
):
    """Downloads hourly streamflow data for a list of gages and saves each as a parquet file"""
    if gage_list_file is not None:
        GAGE_FILE_MAP[gage_type] = gage_list_file
    with open(GAGE_FILE_MAP[gage_type]) as f:
        all_lines = f.readlines()
        sites_collection = [line.strip().split() for line in all_lines]

    output_dir.mkdir(parents=True, exist_ok=True)
    bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
    for site_info in tqdm(sites_collection, desc="Dowloading Gage Hourly Data", bar_format=bar_format):
        if Path(output_dir / f"{site_info[0]}.parquet").exists():
            skipping_msg = f"Parquet for site {site_info[0]} already exists. Skipping..."
            tqdm.write(skipping_msg)
            continue
        if gage_type == "USGS":
            df = get_usgs_streamflow(
                begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), site_info
            )
        elif gage_type == "CADWR":
            df = get_cadwr_streamflow(
                begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), site_info
            )
        elif gage_type == "TXDOT":
            df = get_txdot_streamflow(
                begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), site_info
            )
        elif gage_type == "ENVCA":
            df = get_envca_streamflow(
                begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), site_info, output_dir
            )
        df.to_parquet(output_dir / f"{site_info[0]}.parquet")


if __name__ == "__main__":
    download_usgs_streamflow()
