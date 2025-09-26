"""Contains all click CLI code for accessing hourly streamflow data"""

from pathlib import Path

import click
import icechunk
import numpy as np
import polars as pl
import xarray as xr
from dotenv import load_dotenv

load_dotenv()

BUCKET = "edfs-data"
PREFIX = "streamflow_observations/hourly_streamflow_observations"
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


class NoResultsFoundError(Exception):
    """Passthrough Exception class for catching when an invalid gage ID is provided"""

    pass


def validate_file_extension(ctx, param, value):
    """Validates that the output path is a CSV or parquet file"""
    if value and not value.suffix == ".csv" and not value.suffix == ".parquet":
        raise click.BadParameter(
            "Output file path must have a CSV ('.csv') or parquet ('.parquet') extension."
        )
    return value


@click.command()
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
    help="Output file. Must be a CSV or parquet file extension. Defaults to ${CWD}/${gage-id}.csv",
    callback=validate_file_extension,
)
@click.option(
    "--include-headers",
    "-h",
    type=bool,
    default=False,
    help="Flag to indicate you want CSV headers in the resulting file",
)
def streamflow_observations(
    gage_id: str, start_date: str, end_date: str, output_file: Path, include_headers: bool
):
    """Generates a CSV or parquet file containing the hourly streamflow data for a specific gage ID"""
    if not output_file:
        output_file = Path.cwd() / f"{gage_id}.csv"

    # Get the data from the icechunk store
    storage_config = icechunk.s3_storage(bucket=BUCKET, prefix=PREFIX, region="us-east-1", from_env=True)
    repo = icechunk.Repository.open(storage_config)
    session = repo.writable_session("main")
    ds = xr.open_zarr(session.store, consolidated=False)

    # Slice the dataset to greatly reduce dataframe conversion time
    try:
        ds = ds.sel(time=slice(start_date, end_date), id=gage_id)
    except KeyError as e:
        raise NoResultsFoundError(f"Provided gage_id ({gage_id}) cannot be found in the collection") from e

    # Convert xarray dataset to pandas dataframe for greater control in querying the data
    df = ds.to_dataframe().reset_index()
    pl_df = pl.from_pandas(df)

    # Filter the dataframe based on gage ID and start/end time.
    # Don't include any entries with null q_cms entries
    pl_df = pl_df.filter(pl.col("id") == gage_id)
    pl_df = pl_df.filter((pl.col("time") >= start_date) & (pl.col("time") <= end_date))
    pl_df = pl_df.drop_nulls(subset=["q_cms"])

    if len(pl_df) == 0:
        raise NoResultsFoundError(f"No data was found for {gage_id} in the specified time range")

    # Check if the data has any entries in the 'q_cms_denoted_3' column (if so, include in output file)
    has_q_cms_denoted_3_vals = (~pl_df["q_cms_denoted_3"].is_null()).any()

    # Pare down the number of columns for output
    if has_q_cms_denoted_3_vals:
        pl_df_reordered = pl_df.select(["time", "q_cms", "q_cms_denoted_3"])
    else:
        pl_df_reordered = pl_df.select(["time", "q_cms"])

    # Write finalized output file
    if output_file.suffix == ".csv":
        pl_df_reordered.write_csv(
            output_file, datetime_format="%Y-%m-%d %H:%M:%S", include_header=include_headers
        )
    elif output_file.suffix == ".parquet":
        pl_df_reordered.write_parquet(output_file, compression="lz4", use_pyarrow=True)
    click.echo(f"CSV file created successfully (output path: {output_file})!")

    return len(pl_df)
