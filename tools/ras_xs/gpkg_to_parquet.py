"""A simple script to convert the v2.2 hydrofabric to parquet"""

import argparse
from pathlib import Path

import geopandas as gpd
import pyarrow as pa
from pyarrow import parquet as pq

from icefabric.schemas import ConflatedRasXS, RepresentativeRasXS


def gpkg_to_parquet(input_file: Path, output_folder: Path, schema: str) -> None:
    """Convert geopackage to parquet file.

    Parameters
    ----------
    input_file : Path
        Path to the geopackage file to convert
    output_folder : Path
        Directory where the parquet file will be saved
    schema: str
        The schema to validate against. Either representative XS or all conflated XS

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Converting {input_file} to parquet")

    output_folder.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(input_file)
    gdf = gdf.drop_duplicates()  # drop duplicates

    # NOTE there will be an warning as we're overriding the geometry. This is fine for now
    gdf["geometry"] = gdf["geometry"].to_wkb()

    # Create PyArrow table with schema validation
    if schema == "representative":
        table = pa.Table.from_pandas(
            gdf[RepresentativeRasXS.columns()], schema=RepresentativeRasXS.arrow_schema()
        )
    elif schema == "conflated":
        table = pa.Table.from_pandas(gdf[ConflatedRasXS.columns()], schema=ConflatedRasXS.arrow_schema())
    else:
        raise ValueError("Schema not found for your inputted XS file")

    # Write parquet file
    output_path = output_folder / f"{input_file.stem}.parquet"
    pq.write_table(table, output_path)

    print(f"Successfully converted to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert geopackage files to parquet format")

    parser.add_argument("--gpkg", type=Path, required=True, help="Path to the geopackage file to convert")
    parser.add_argument(
        "--schema",
        type=str,
        choices=["representative", "conflated"],
        required=True,
        help="The schema to validate against. Either representative XS or all conflated XS",
    )
    parser.add_argument(
        "--output-folder",
        type=Path,
        default=Path.cwd(),
        help="Output directory for parquet file (default is cwd)",
    )

    args = parser.parse_args()
    gpkg_to_parquet(input_file=args.gpkg, output_folder=args.output_folder, schema=args.schema)
