"""A simple script to convert the NHF to parquet"""

import argparse
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyarrow as pa
import pyogrio
from pyarrow import parquet as pq
from pyogrio.errors import DataLayerError

from icefabric.schemas.iceberg_tables import nhf_layers


def nhf_gpkg_to_parquet(input_file: Path, output_folder: Path, strict: bool = False) -> None:
    """Convert geopackage to parquet file.

    Parameters
    ----------
    input_file : Path
        Path to the geopackage file to convert
    output_folder : Path
        Directory where the parquet file will be saved
    strict : bool
        Validate that every source layer has a supported schema, reject required
        or unexpected columns, and confirm every source layer is converted.

    Raises
    ------
    FileNotFoundError
        If the input file doesn't exist
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    source_layers = set(pyogrio.list_layers(input_file)[:, 0])
    unsupported_layers = source_layers - set(nhf_layers)
    if strict and unsupported_layers:
        raise ValueError(
            "GeoPackage contains layers without an Iceberg schema: " + ", ".join(sorted(unsupported_layers))
        )

    output_folder.mkdir(parents=True, exist_ok=True)
    converted_layers: set[str] = set()
    for layer, schema in nhf_layers.items():
        if layer not in source_layers:
            print(f"No layer existing for: {layer}")
            continue

        print(f"Converting {layer} to parquet")

        if strict:
            info = pyogrio.read_info(input_file, layer=layer)
            source_columns = set(info["fields"])
            if info["geometry_type"] is not None:
                source_columns.add("geometry")
            expected_columns = set(schema.columns())
            missing_columns = expected_columns - source_columns
            required_columns = {field.name for field in schema.arrow_schema() if not field.nullable}
            missing_required = missing_columns & required_columns
            unexpected_columns = source_columns - expected_columns
            if missing_required or unexpected_columns:
                raise ValueError(
                    f"Column mismatch for {layer}: "
                    f"missing_required={sorted(missing_required)}, "
                    f"unexpected={sorted(unexpected_columns)}"
                )
            if missing_columns:
                print(f"Padding nullable columns absent from {layer}: " + ", ".join(sorted(missing_columns)))

        try:
            gdf = gpd.read_file(input_file, layer=layer)
        except DataLayerError as exc:
            if strict:
                raise ValueError(f"Required NHF layer is missing: {layer}") from exc
            print(f"No layer existing for: {layer}")
            continue
        if "geometry" in gdf.columns:
            geometry_wkb = gdf.geometry.to_wkb()
            # Drop the GeoDataFrame's active geometry before assigning WKB.
            gdf = pd.DataFrame(gdf.drop(columns="geometry"))
            gdf["geometry"] = geometry_wkb

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
                and (pa.types.is_integer(field.type) or pa.types.is_floating(field.type))
            ):
                gdf[field.name] = pd.to_numeric(gdf[field.name], errors="coerce")

        # Create PyArrow table with schema validation
        table = pa.Table.from_pandas(gdf[schema.columns()], schema=arrow_schema, preserve_index=False)

        # Write parquet file
        output_path = output_folder / f"{layer}.parquet"
        pq.write_table(table, output_path)
        converted_layers.add(layer)
        print(f"Successfully converted to {output_path}")

    if strict and converted_layers != source_layers:
        missing = source_layers - converted_layers
        raise ValueError("Not all GeoPackage layers were converted: " + ", ".join(sorted(missing)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert geopackage files to parquet format")

    parser.add_argument("--gpkg", type=Path, required=True, help="Path to the geopackage file to convert")
    parser.add_argument(
        "--output-folder",
        type=Path,
        default=Path.cwd(),
        help="Output directory for parquet file (default is cwd)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail unless every GeoPackage layer has a schema and is converted",
    )

    args = parser.parse_args()
    nhf_gpkg_to_parquet(
        input_file=args.gpkg,
        output_folder=args.output_folder,
        strict=args.strict,
    )
