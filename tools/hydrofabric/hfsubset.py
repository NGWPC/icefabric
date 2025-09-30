"""A script to subset the hydrofabric"""

import argparse
from pathlib import Path

from pyiceberg.catalog import load_catalog

from icefabric.helpers import load_creds
from icefabric.hydrofabric import subset
from icefabric.schemas import IdType

load_creds(dir=Path.cwd())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 endpoint")

    parser.add_argument("--hf-uri", help="the gauge # to subset from")
    parser.add_argument("--output-file", help="Where the subset should be output [as a geopackage]")

    args = parser.parse_args()

    if args.output_file is None:
        output_file = Path("subset.gpkg")
    else:
        output_file = Path(args.output_file)
    subset(
        catalog=load_catalog("glue"),
        identifier=f"gages-{args.hf_uri}",
        id_type=IdType.HL_URI,
        output_file=output_file,
    )
    print(f"Subset file written to: {output_file}")
