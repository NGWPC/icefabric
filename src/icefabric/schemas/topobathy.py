"""Contains all schemas and enums for topobathy definitions in the NGWPC S3"""

from enum import Enum

from icefabric.builds.icechunk_s3_module import S3Path

TOPO_BP = "surface/nws-topobathy"
TOPO_NOS = f"{TOPO_BP}/nws-nos-surveys"


class FileType(Enum):
    """
    Archival weather file types

    Enum class for instantiating different archival weather file
    formats. Used when virtualizing and collecting files.
    """

    GEOTIFF = ".tif"
    NETCDF = ".nc"


class NGWPCLocations(Enum):
    """
    Important NGWPC S3 locations

    Enum class for instantiating S3Paths corresponding to the
    icechunk stores, as well as the reference locations for virtualized
    stores.
    """

    SNODAS_REF = ("ngwpc-forcing", "snodas_nc_v4")
    SNODAS_V3 = ("ngwpc-forcing", "snodas_nc")
    SNODAS_IC = ("hydrofabric-data", "forcing/snodas")
    NLCD_REF = ("ngwpc-hydrofabric", "NLCD_Land_Cover_CONUS")
    NLCD_IC = ("hydrofabric-data", "land-cover/NLCD-Land-Cover")
    TOPO_AK_10M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_alaska_10m")
    TOPO_AK_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_alaska_30m")
    TOPO_CONUS_ATL_GULF_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_conus_atlantic_gulf_30m")
    TOPO_CONUS_PAC_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_conus_pacific_30m")
    TOPO_GREAT_LAKES_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_great_lakes_30m")
    TOPO_HA_10M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_hawaii_10m")
    TOPO_HA_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_hawaii_30m")
    TOPO_PR_USVI_10M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_pr_usvi_10m")
    TOPO_PR_USVI_30M_IC = ("hydrofabric-data", f"{TOPO_BP}/tbdem_pr_usvi_30m")
    TOPO_ALBEMARLE_SOUND_IC = ("hydrofabric-data", f"{TOPO_NOS}/Albemarle_Sound_NOS_NCEI")
    TOPO_CHESAPEAKE_BAY_IC = ("hydrofabric-data", f"{TOPO_NOS}/Chesapeake_Bay_NOS_NCEI")
    TOPO_MOBILE_BAY_IC = ("hydrofabric-data", f"{TOPO_NOS}/Mobile_Bay_NOS_NCEI")
    TOPO_TANGIER_SOUND_IC = ("hydrofabric-data", f"{TOPO_NOS}/Tangier_Sound_NOS_NCEI")

    def __init__(self, bucket, prefix):
        self.path = S3Path(bucket, prefix)


class NGWPCTestLocations(Enum):
    """
    Important NGWPC S3 locations

    Enum class for instantiating S3Paths corresponding to the
    icechunk stores, as well as the reference locations for virtualized
    stores.
    """

    # SNODAS_IC = ("edfs-data", "forcing/snodas")  # commenting out until data can be moved from data to test bucket
    NLCD_IC = ("edfs-data", "land-cover/NLCD-Land-Cover")
    TOPO_AK_10M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_alaska_10m")
    TOPO_AK_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_alaska_30m")
    TOPO_CONUS_ATL_GULF_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_conus_atlantic_gulf_30m")
    TOPO_CONUS_PAC_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_conus_pacific_30m")
    TOPO_GREAT_LAKES_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_great_lakes_30m")
    TOPO_HA_10M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_hawaii_10m")
    TOPO_HA_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_hawaii_30m")
    TOPO_PR_USVI_10M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_pr_usvi_10m")
    TOPO_PR_USVI_30M_IC = ("edfs-data", f"{TOPO_BP}/tbdem_pr_usvi_30m")
    TOPO_ALBEMARLE_SOUND_IC = ("edfs-data", f"{TOPO_NOS}/Albemarle_Sound_NOS_NCEI")
    TOPO_CHESAPEAKE_BAY_IC = ("edfs-data", f"{TOPO_NOS}/Chesapeake_Bay_NOS_NCEI")
    TOPO_MOBILE_BAY_IC = ("edfs-data", f"{TOPO_NOS}/Mobile_Bay_NOS_NCEI")
    TOPO_TANGIER_SOUND_IC = ("edfs-data", f"{TOPO_NOS}/Tangier_Sound_NOS_NCEI")

    def __init__(self, bucket, prefix):
        self.path = S3Path(bucket, prefix)
