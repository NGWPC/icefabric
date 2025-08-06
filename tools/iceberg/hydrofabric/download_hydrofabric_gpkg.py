"""A script to download the Hydrofabric to disk as a geopackage"""

import argparse
from pathlib import Path

import geopandas as gpd
from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.exceptions import NoSuchTableError
from tqdm import tqdm

from icefabric.helpers import load_creds

load_creds(dir=Path.cwd())


def download_hydrofabric(catalog: Catalog, namespace: str, output_folder: Path, crs: str) -> None:
    """Build the RAS XS table in a PyIceberg warehouse.

    Parameters
    ----------
    catalog : Catalog
        The PyIceberg catalog object
    namespace: str
        Path to the parquet file to upload to the warehouse
    output_folder: Path
        Output directory for saving the hydrofabric gpkg
    crs: str
        A string representing the CRS to set in the gdf
    """
    layers = [
        "divide-attributes",
        "divides",
        "flowpath-attributes",
        "flowpath-attributes-ml",
        "flowpaths",
        "hydrolocations",
        "lakes",
        "network",
        "nexus",
        "pois",
    ]
    output_layers = {}
    for layer in tqdm(layers, desc=f"Exporting {namespace} tables", total=len(layers)):
        try:
            table = catalog.load_table(f"{namespace}.{layer}")
            df = table.scan().to_pandas()
            if "geometry" in df.columns:
                output_layers[layer] = gpd.GeoDataFrame(
                    df, geometry=gpd.GeoSeries.from_wkb(df["geometry"]), crs=crs
                )
            else:
                output_layers[layer] = df
        except NoSuchTableError:
            print(f"No table found for layer: {layer}.")

    output_folder.mkdir(exist_ok=True)
    output_file = output_folder / f"{namespace}.gpkg"
    print("Saving hydrofabric to disk")
    for table_name, _layer in output_layers.items():
        gpd.GeoDataFrame(_layer).to_file(output_file, layer=table_name, driver="GPKG")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download the latest HF production snapshot")

    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--namespace", type=str, required=True, help="The hydrofabric namespace (domain) to download"
    )
    parser.add_argument(
        "--output-folder",
        type=Path,
        default=Path.cwd(),
        help="Output directory for saving the hydrofabric gpkg",
    )
    parser.add_argument(
        "--crs",
        type=str,
        default="EPSG:5070",
        help="The CRS to save the outputted .gpkg to (default is EPSG:5070). Change for oCONUS domains.",
    )
    args = parser.parse_args()

    catalog = load_catalog(args.catalog)
    download_hydrofabric(
        catalog=catalog, namespace=args.namespace, output_folder=args.output_folder, crs=args.crs
    )
