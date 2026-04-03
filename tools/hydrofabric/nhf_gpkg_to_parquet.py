"""A simple script to convert the NHF to parquet"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyarrow as pa
from pyarrow import parquet as pq
from pyogrio.errors import DataLayerError

from icefabric.helpers import load_creds
from icefabric.schemas.iceberg_tables import nhf_layers

load_creds()


def nhf_gpkg_to_parquet(input_file: Path, output_folder: Path) -> None:
    """Convert geopackage to parquet file.

    Parameters
    ----------
    input_file : Path
        Path to the geopackage file to convert
    output_folder : Path
        Directory where the parquet file will be saved

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    """
    for layer, schema in nhf_layers.items():
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        print(f"Converting {layer} to parquet")

        output_folder.mkdir(parents=True, exist_ok=True)

        try:
            gdf = gpd.read_file(input_file, layer=layer)
        except DataLayerError:
            print(f"No layer existing for: {layer}")
            continue
        if "geometry" in gdf.columns:
            gdf["geometry"] = gdf["geometry"].to_wkb()
            # Drop the GeoDataFrame's geometry reference
            gdf = pd.DataFrame(gdf)

        # Add missing nullable columns as null (handles domain differences)
        for col in schema.columns():
            if col not in gdf.columns:
                gdf[col] = None

        # Coerce string-encoded numeric columns to match the arrow schema
        arrow_schema = schema.arrow_schema()
        for field in arrow_schema:
            if (
                field.name in gdf.columns
                and gdf[field.name].dtype == object
                and pa.types.is_integer(field.type)
            ):
                gdf[field.name] = pd.to_numeric(gdf[field.name], errors="coerce")

        # Create PyArrow table with schema validation
        table = pa.Table.from_pandas(gdf[schema.columns()], schema=arrow_schema)

        # Write parquet file
        output_path = output_folder / f"{layer}.parquet"
        pq.write_table(table, output_path)
        print(f"Successfully converted to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert geopackage files to parquet format")

    parser.add_argument("--gpkg", type=Path, required=True, help="Path to the geopackage file to convert")
    parser.add_argument(
        "--output-folder",
        type=Path,
        default=Path.cwd(),
        help="Output directory for parquet file (default is cwd)",
    )

    args = parser.parse_args()
    nhf_gpkg_to_parquet(input_file=args.gpkg, output_folder=args.output_folder)
