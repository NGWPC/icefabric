"""A simple script to convert the v2.2 hydrofabric to parquet"""

import argparse
from pathlib import Path

import fiona
import geopandas as gpd

from icefabric.helpers import load_creds

load_creds(dir=Path.cwd())


def gpkg_to_parquet(input_file: str, output_folder: str = "../../data/") -> None:
    """A function to convert geopackages to parquet files

    Parameters
    ----------
    input_file : str
        the gpkg to convert
    """
    available_layers = fiona.listlayers(input_file)
    print(f"Layers in GeoPackage: {available_layers}")

    for layer in available_layers:
        gdf = gpd.read_file(input_file, layer=layer)
        output_file = f"{output_folder}/{layer}.parquet"
        gdf.to_parquet(output_file)
        print(f"Converted layer '{layer}' to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 endpoint")

    parser.add_argument("--gpkg", help="The local gpkg to convert into a parquet file")
    parser.add_argument("--output-folder", help="The output folder for to save the parquet file")

    args = parser.parse_args()
    gpkg_to_parquet(input_file=args.gpkg, output_folder=args.output_folder)
