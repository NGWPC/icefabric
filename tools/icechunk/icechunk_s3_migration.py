import argparse
import os

from dotenv import load_dotenv

from icefabric.schemas import NGWPCLocations

from .icechunk_testing import topo_push_test

load_dotenv()


def migrate_all_icechunks(attr_name: str) -> None:
    """Converts & migrates TIFFs from local to cloud.

    Parameters
    ----------
    attr_name: str
        Attribute name of interest for a given TIFF.
    """
    # Extract list of TIFFs from local
    local_list = []
    for _, _, files in os.walk("./"):
        for file in files:
            if file.endswith(".tiff"):
                local_list.append(file.lower())

    # Maps the S3 paths to TIFFs
    topo_fn2s3_map = {}
    for fn in local_list:
        if "hawaii_10m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_HA_10M_IC.path] = "tbdem_hawaii_10m.tiff"
        elif "hawaii_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_HA_30M_IC.path] = "tbdem_hawaii_30m.tiff"
        elif "conus_atlantic_gulf_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_CONUS_ATL_GULF_30M_IC.path] = (
                "tbdem_conus_atlantic_gulf_30m.tiff"
            )
        elif "conus_pacific_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_CONUS_PAC_30M_IC.path] = "tbdem_conus_pacific_30m.tiff"
        elif "pr_usvi_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_PR_USVI_30M_IC.path] = "tbdem_pr_usvi_30m.tiff"
        elif "pr_usvi_10m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_PR_USVI_10M_IC.path] = "tbdem_pr_usvi_10m.tiff"
        elif "alaska_10m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_AK_10M_IC.path] = "tbdem_alaska_10m.tiff"
        elif "alaska_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_AK_30M_IC.path] = "tbdem_alaska_30m.tiff"
        elif "great_lakes_30m" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_GREAT_LAKES_30M_IC.path] = "tbdem_great_lakes_30m.tiff"
        elif "albemarle_sound_nos_ncei" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_ALBEMARLE_SOUND_IC.path] = "Albemarle_Sound_NOS_NCEI.tiff"
        elif "chesapeake_bay_nos_ncei" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_CHESAPEAKE_BAY_IC.path] = "Chesapeake_Bay_NOS_NCEI.tiff"
        elif "mobile_bay_nos_ncei" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_MOBILE_BAY_IC.path] = "Mobile_Bay_NOS_NCEI.tiff"
        elif "tangier_sound_nos_ncei-002" in fn:
            topo_fn2s3_map[NGWPCLocations.TOPO_TANGIER_SOUND_IC.path] = "Tangier_Sound_NOS_NCEI-002.tiff"

    # Migration of all captured TIFFs to cloud.
    for s3_path, fn in topo_fn2s3_map.items():
        if fn:
            topo_push_test(tiff_fp=f"./{fn}", attr_name=attr_name, new_ic_repo=s3_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to write an icechunk store")

    parser.add_argument("--attr", help="The attribute that is to be built to icechunk")

    args = parser.parse_args()
    migrate_all_icechunks(attr_name=args.attr)
