"""A function to convert the topobathy data into a tif file"""

import os
from pathlib import Path

from icefabric.helpers import convert_topobathy_to_tiff, load_creds
from icefabric.schemas import NGWPCLocations

load_creds(dir=Path.cwd())

if __name__ == "__main__":
    output_dir = "./temp_tb_data"
    os.makedirs(output_dir, exist_ok=True)

    # all 30 m topobathy layers
    ic_rasters = [f for f in NGWPCLocations._member_names_ if "TOPO" and "30M" in f]

    convert_topobathy_to_tiff(output_dir, ic_rasters)
