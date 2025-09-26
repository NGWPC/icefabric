"""A sample script to generate CFE IPEs"""

import argparse

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

# param_file = "../src/icefabric_api/data/cfe_params.csv"
# gpkg_file = "../src/icefabric_tools/test/data/gages-08070000.gpkg"
load_dotenv()


def create_module_params(param_file: str, gpkg_file: str) -> None:
    """Creates module initial parameter estimates

    Parameters
    ----------
    param_file : str
        the initial parameters file
    gpkg_file : str
        the hydrofabric gpkg file
    """
    divides = gpd.read_file(gpkg_file, layer="divides")
    divides = divides["divide_id"].to_list()

    module_params = pd.read_csv(param_file)
    param_values = module_params[["name", "default_value"]]

    for divide in divides:
        cfg_file = f"{divide}_bmi_cfg_cfe.txt"
        f = open(cfg_file, "x")

        for _, row in param_values.iterrows():
            key = row["name"]
            value = row["default_value"]
            f.write(f"{key}={value}\n")

        f.close()

    params_calibratable = module_params.loc[module_params["calibratable"] == "TRUE"]
    params_calibratable.to_json("out.json", orient="split")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to make initial parameter estimates")

    parser.add_argument("--params", help="The initial parameters file")
    parser.add_argument("--gpkg", help="The hydrofabric gpkg file")

    args = parser.parse_args()
    create_module_params(param_file=args.params, gpkg_file=args.gpkg)
