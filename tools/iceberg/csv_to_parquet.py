import argparse

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from icefabric.schemas import ParameterMetadata


def csv_to_parquet(path, filename):
    """Converts the parameter metadata in CSV format to Parquet.

    Parameters
    ----------
    file_dir : str
        The directory to parameter metadata parquet file
    filename: str
        The filename of the parquet file
    """
    csv_file = f"{path}/{filename}"
    parquet_file = filename.split(".")[0]
    parquet_file = f"{path}/{parquet_file}.parquet"

    df = pd.read_csv(csv_file)
    table = pa.Table.from_pandas(df, schema=ParameterMetadata.arrow_schema())
    pq.write_table(table, parquet_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="a script to convert a csv file to parquet")

    parser.add_argument("--path", help="the path to the csv file and converted parquet file")
    parser.add_argument("--file", help="the CSV filename")

    args = parser.parse_args()
    csv_to_parquet(path=args.path, filename=args.file)
