import argparse
from pathlib import Path

from icefabric.hydrofabric import subset_nhf

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subset hydrofabric by flowpath, gage, or VPU.")
    parser.add_argument("-c", "--catalog", action="store_true", help="Use Iceberg catalog")
    parser.add_argument("-p", "--parquet-dir", type=Path, help="Path to parquet directory")
    parser.add_argument("-f", "--flowpath-id", type=int, help="Origin flowpath ID (traces upstream)")
    parser.add_argument("-g", "--gage-id", type=str, help="Gage ID (traces upstream from gage's flowpath)")
    parser.add_argument("-v", "--vpu-id", type=str, help="VPU ID (extracts entire VPU)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output GeoPackage path")

    args = parser.parse_args()
    _ = subset_nhf(
        flowpath_id=args.flowpath_id,
        gage_id=args.gage_id,
        vpu_id=args.vpu_id,
        catalog=args.catalog,
        parquet_dir=args.parquet_dir,
        output=args.output,
    )
