"""Contains all click CLI code for NWM modules"""

from pathlib import Path

import click
import icechunk
import numpy as np
import polars as pl
import xarray as xr
from dotenv import load_dotenv

from icefabric.schemas.hydrofabric import StreamflowDataSources

load_dotenv()

BUCKET = "edfs-data"
PREFIX = "streamflow_observations"
TIME_FORMATS = [
    "%Y",
    "%Y-%m",
    "%Y-%m-%d",
    "%Y-%m-%d %H",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
]
MIN_DT = str(np.datetime64("1678-01-01T00:00:00.000000", "ms"))
MAX_DT = str(np.datetime64("2262-04-11T23:47:16.854775", "ms"))


def validate_file_extension(ctx, param, value):
    """Validates that the output path is a CSV file"""
    if value and not value.suffix == ".csv":
        raise click.BadParameter("Output file path must have a CSV ('.csv') extension.")
    return value


@click.command()
@click.option(
    "--data-source",
    "-d",
    type=click.Choice([module.value for module in StreamflowDataSources], case_sensitive=False),
    help="The data source for the USGS gage id",
)
@click.option(
    "--gage-id",
    "-g",
    type=str,
    help="The Gauge ID you want the hourly streamflow data from",
)
@click.option(
    "--start-date",
    "-s",
    type=click.DateTime(formats=TIME_FORMATS),
    default=MIN_DT,
    help="Start of the hourly streamflow timestamp range to be included. If not specified, time range defaults to having no minimum.",
)
@click.option(
    "--end-date",
    "-e",
    type=click.DateTime(formats=TIME_FORMATS),
    default=MAX_DT,
    help="End of the hourly streamflow timestamp range to be included. If not specified, time range defaults to having no maximum.",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Output CSV file. Must be a CSV file extension. Defaults to ${CWD}/${gage-id}.csv",
    callback=validate_file_extension,
)
def streamflow_observations(
    data_source: str, gage_id: str, start_date: str, end_date: str, output_file: Path
):
    """Generates a CSV file containing the hourly streamflow data for a specific gage ID"""
    if not output_file:
        output_file = Path.cwd() / f"{gage_id}.csv"
    ic_store_type = "usgs" if data_source == "USGS" else "envca_cadwr_txdot"

    # Get the data from the icechunk store
    storage_config = icechunk.s3_storage(
        bucket=BUCKET, prefix=f"{PREFIX}/{ic_store_type}_observations", region="us-east-1", from_env=True
    )
    repo = icechunk.Repository.open(storage_config)
    session = repo.writable_session("main")
    ds = xr.open_zarr(session.store, consolidated=False)

    # Slice the dataset to greatly reduce dataframe conversion time
    ds = ds.sel(time=slice(start_date, end_date), id=gage_id)

    # Convert xarray dataset to pandas dataframe for greater control in querying the data
    df = ds.to_dataframe().reset_index()
    pl_df = pl.from_pandas(df)

    # Filter the dataframe based on gage ID and start/end time.
    # Don't include any entries with null q_cms entries
    pl_df = pl_df.filter(pl.col("gage_type") == data_source)
    pl_df = pl_df.filter(pl.col("id") == gage_id)
    pl_df = pl_df.filter((pl.col("time") >= start_date) & (pl.col("time") <= end_date))
    pl_df = pl_df.drop_nulls(subset=["q_cms"])

    # Check if the data has any entries in the 'q_cms_denoted_3' column (if so, include in CSV)
    has_q_cms_denoted_3_vals = (~pl_df["q_cms_denoted_3"].is_null()).any()

    # Pare down the number of CSV columns for output
    if has_q_cms_denoted_3_vals:
        pl_df_reordered = pl_df.select(["time", "q_cms", "q_cms_denoted_3"])
    else:
        pl_df_reordered = pl_df.select(["time", "q_cms"])

    # Write finalized CSV file
    pl_df_reordered.write_csv(output_file, datetime_format="%Y-%m-%d %H:%M:%S")
    click.echo(f"CSV file created successfully (output path: {output_file})!")
