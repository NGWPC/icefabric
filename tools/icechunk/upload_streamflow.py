from pathlib import Path

import click
import icechunk
import numpy as np
import pandas as pd
from icechunk.xarray import to_icechunk
from tqdm import tqdm

from icefabric.helpers import load_creds
from tools.icechunk.download_streamflow import GAGE_FILE_MAP

load_creds()


def batch_list(lst, batch_size):
    """Splits a list into smaller batches of a specified size"""
    batches = []
    for i in range(0, len(lst), batch_size):
        batches.append(lst[i : i + batch_size])
    return batches


@click.command()
@click.option("--overwrite", type=bool, default=False, help="Overwrite the existing Icechunk store")
@click.option(
    "--parquets-location",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("data/USGS_streamflow_parquets"),
    help="Local directory containing the parquet files to upload",
)
@click.option(
    "--bucket", type=str, default="ngwpc-hydrofabric", help="S3 bucket that the Icechunk store is hosted in"
)
@click.option(
    "--prefix", type=str, default="usgs_observations", help="S3 prefix that corresponds to the Icechunk store"
)
@click.option(
    "--gage-type",
    type=click.Choice(list(GAGE_FILE_MAP.keys())),
    default="USGS",
    help="Which type of gage this upload corresponds to.",
)
@click.option("--batch-size", type=int, default=100, help="Number of files to process in each batch")
def upload_usgs_streamflow(
    overwrite: bool, parquets_location: Path, bucket: str, prefix: str, gage_type: str, batch_size: int
):
    """Uploads USGS streamflow parquet files to an Icechunk store in S3"""
    storage_config = icechunk.s3_storage(bucket=bucket, prefix=prefix, region="us-east-1", from_env=True)
    repo = icechunk.Repository.open_or_create(storage_config)

    if overwrite:
        message = f"Overwrote icechunk store with new {gage_type} streamflow data"
    else:
        message = f"Added new {gage_type} sites"
    with repo.transaction(branch="main", message=message) as store:
        files = [file for file in parquets_location.glob("*.parquet") if file.is_file()]
        file_batches = batch_list(files, batch_size)
        i = 0
        bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        for batch in tqdm(file_batches, bar_format=bar_format):
            dataframes = []
            for file in batch:
                df = pd.read_parquet(file)
                if "q_cms_denoted_3" not in df.columns:
                    df["q_cms_denoted_3"] = np.nan
                    df["q_cms_denoted_3"] = df["q_cms_denoted_3"].astype(float)
                dataframes.append(df)
            batch_ds = pd.concat(dataframes, axis=0).to_xarray()
            batch_ds.coords["id"] = batch_ds.coords["id"].astype("<U15")
            if overwrite and i == 0:
                to_icechunk(batch_ds, session=store.session, mode="w")
                print(
                    f"Overwrote (or made new) icechunk store with {gage_type} streamflow data (batch {i + 1}/{len(file_batches)})"
                )
            else:
                to_icechunk(batch_ds, session=store.session, append_dim="id")
                print(f"Appended new {gage_type} sites to icechunk store (batch {i + 1}/{len(file_batches)})")
            i += 1
    print(f"{gage_type} parquet data successfully uploaded to Icechunk store @ s3://{bucket}/{prefix}.")
    print(f"Commit message: {message}")


if __name__ == "__main__":
    upload_usgs_streamflow()
