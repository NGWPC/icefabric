"""
Contains the PyIceberg Table schemas for the updated Hydrofabric v2.2 data model tables

NOTE - THIS IS A WORK IN PROGRESS
"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, BooleanType, DoubleType, FloatType, LongType, NestedField, StringType


class Divides:
    """
    The schema for the divides table

    Attributes
    ----------
    div_id : int
        Unique divide identifier
    vpu_id : str
        Vector Processing Unit identifier
    type : str
        Divide Type (one of independent, aggregate, connectors)
    area_sqkm : float
        Incremental Areas of Divide [square kilometers]
    bexp_mode : float
        beta exponent on Clapp-Hornberger (1978) soil water relations
    isltyp_mode : float
        Dominent soil type category
    ivgtyp_mode : float
        Dominent vegetation type category
    dksat_geomean : float
        Saturated hydraulic conductivity
    psisat_geomean : float
        Saturated capillary head
    cwpvt_mean : float
        Empirical canopy wind parameter
    msfno_mean : float
        Melt factor for snow depletion curve
    refkdt_mean : float
        Reference soil infiltration parameter
    mp_mean : float
        Slope of Conductance to photosynthesis relationship
    quartz_mean : float
        Mean soil quartz content
    slope1km_mean : float
        Modifies the gradient of the hydraulic head at the soil bottom
    smcmax_mean : float
        Saturated soil moisture content
    smcwlt_mean : float
        Wilting point soil moisture content
    vcmx_mean : float
        Maximum rate of carboxylation at 25 C
    imperv_mean : float
        Percentage of catchment with an impervious surface
    twi_q10 : float
        Topographic wetness index 10th percentile
    twi_q20 : float
        Topographic wetness index 20th percentile
    twi_q25 : float
        Topographic wetness index 1st quartile
    twi_q30 : float
        Topographic wetness index 30th percentile
    twi_q40 : float
        Topographic wetness index 40th percentile
    twi_q50 : float
        Topographic wetness index 2nd quartile
    twi_q60 : float
        Topographic wetness index 60th percentile
    twi_q70 : float
        Topographic wetness index 70th percentile
    twi_q75 : float
        Topographic wetness index 3rd quartile
    twi_q80 : float
        Topographic wetness index 80th percentile
    twi_q90 : float
        Topographic wetness index 90th percentile
    twi_q100 : float
        Topographic wetness index 4th quartile
    cgw : float
        Groundwater Coefficient
    expon : float
        Groundwater Exponent
    max_gw_storage : float
        The total height of the baseflow "bucket"
    elevation_mean : float
        Terrain elevation
    slope250m_mean : float
        Terrain slope
    aspect_circmean : float
        Terrain aspect
    glacier_percent : float
        Percentage of glacier cover within the divide
    lat: float
        Latitude of the divide (in WGS84 degrees)
    lon: float
        Longitude of the divide (in WGS84 degrees)
    geometry : binary
        Spatial Geometry (MULTIPOLYGON format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the divides table
        """
        return [
            "div_id",
            "vpu_id",
            "type",
            "area_sqkm",
            "bexp_mode",
            "isltyp_mode",
            "ivgtyp_mode",
            "dksat_geomean",
            "psisat_geomean",
            "cwpvt_mean",
            "mfsno_mean",
            "refkdt_mean",
            "mp_mean",
            "quartz_mean",
            "slope1km_mean",
            "smcmax_mean",
            "smcwlt_mean",
            "vcmx_mean",
            "imperv_mean",
            "twi_q10",
            "twi_q20",
            "twi_q25",
            "twi_q30",
            "twi_q40",
            "twi_q50",
            "twi_q60",
            "twi_q70",
            "twi_q75",
            "twi_q80",
            "twi_q90",
            "twi_q100",
            "cgw",
            "expon",
            "max_gw_storage",
            "elevation_mean",
            "slope250m_mean",
            "aspect_circmean",
            "glacier_percent",
            "lat",
            "lon",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the divides table
        """
        desc = [
            "Unique divide identifier",
            "Vector Processing Unit identifier",
            "Divide Type (one of independent, aggregate, connectors)",
            "Incremental Areas of Divide [square kilometers]",
            "beta exponent on Clapp-Hornberger (1978) soil water relations",
            "Dominent soil type category",
            "Dominent vegetation type category",
            "Saturated hydraulic conductivity",
            "Saturated capillary head",
            "Empirical canopy wind parameter",
            "Melt factor for snow depletion curve",
            "Reference soil infiltration parameter",
            "Slope of Conductance to photosynthesis relationship",
            "Mean soil quartz content",
            "modifies the gradient of the hydraulic head at the soil bottom",
            "Saturated soil moisture content",
            "Wilting point soil moisture content",
            "Maximum rate of carboxylation at 25 C",
            "Percentage of catchment with an impervious surface",
            "Topographic wetness index 10th percentile",
            "Topographic wetness index 20th percentile",
            "Topographic wetness index 1st quartile",
            "Topographic wetness index 30th percentile",
            "Topographic wetness index 40th percentile",
            "Topographic wetness index 2nd quartile",
            "Topographic wetness index 60th percentile",
            "Topographic wetness index 70th percentile",
            "Topographic wetness index 3rd quartile",
            "Topographic wetness index 80th percentile",
            "Topographic wetness index 90th percentile",
            "Topographic wetness index 4th quartile",
            "Groundwater Coefficient",
            "Groundwater Exponent",
            "The total height of the baseflow bucket",
            "Terrain elevation",
            "Terrain slope",
            "Terrain aspect",
            "Percentage of glacier cover within the divide",
            "Latitude of the divide (in WGS84 degrees)",
            "Longitude of the divide (in WGS84 degrees)",
            "GeometrySpatial Geometry (MULTIPOLYGON format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "div_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "vpu_id", StringType(), required=False, doc=desc[1]),
            NestedField(3, "type", StringType(), required=False, doc=desc[2]),
            NestedField(4, "area_sqkm", DoubleType(), required=False, doc=desc[3]),
            NestedField(5, "bexp_mode", DoubleType(), required=False, doc=desc[4]),
            NestedField(6, "isltyp_mode", DoubleType(), required=False, doc=desc[5]),
            NestedField(7, "ivgtyp_mode", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "dksat_geomean", DoubleType(), required=False, doc=desc[7]),
            NestedField(9, "psisat_geomean", DoubleType(), required=False, doc=desc[8]),
            NestedField(10, "cwpvt_mean", DoubleType(), required=False, doc=desc[9]),
            NestedField(11, "mfsno_mean", DoubleType(), required=False, doc=desc[10]),
            NestedField(12, "refkdt_mean", DoubleType(), required=False, doc=desc[11]),
            NestedField(13, "mp_mean", DoubleType(), required=False, doc=desc[12]),
            NestedField(14, "quartz_mean", DoubleType(), required=False, doc=desc[13]),
            NestedField(15, "slope1km_mean", DoubleType(), required=False, doc=desc[14]),
            NestedField(16, "smcmax_mean", DoubleType(), required=False, doc=desc[15]),
            NestedField(17, "smcwlt_mean", DoubleType(), required=False, doc=desc[16]),
            NestedField(18, "vcmx_mean", DoubleType(), required=False, doc=desc[17]),
            NestedField(19, "imperv_mean", DoubleType(), required=False, doc=desc[18]),
            NestedField(20, "twi_q10", DoubleType(), required=False, doc=desc[19]),
            NestedField(21, "twi_q20", DoubleType(), required=False, doc=desc[20]),
            NestedField(22, "twi_q25", DoubleType(), required=False, doc=desc[21]),
            NestedField(23, "twi_q30", DoubleType(), required=False, doc=desc[22]),
            NestedField(24, "twi_q40", DoubleType(), required=False, doc=desc[23]),
            NestedField(25, "twi_q50", DoubleType(), required=False, doc=desc[24]),
            NestedField(26, "twi_q60", DoubleType(), required=False, doc=desc[25]),
            NestedField(27, "twi_q70", DoubleType(), required=False, doc=desc[26]),
            NestedField(28, "twi_q75", DoubleType(), required=False, doc=desc[27]),
            NestedField(29, "twi_q80", DoubleType(), required=False, doc=desc[28]),
            NestedField(30, "twi_q90", DoubleType(), required=False, doc=desc[29]),
            NestedField(31, "twi_q100", DoubleType(), required=False, doc=desc[30]),
            NestedField(32, "cgw", DoubleType(), required=False, doc=desc[31]),
            NestedField(33, "expon", DoubleType(), required=False, doc=desc[32]),
            NestedField(34, "max_gw_storage", DoubleType(), required=False, doc=desc[33]),
            NestedField(35, "elevation_mean", DoubleType(), required=False, doc=desc[34]),
            NestedField(36, "slope250m_mean", DoubleType(), required=False, doc=desc[35]),
            NestedField(37, "aspect_circmean", DoubleType(), required=False, doc=desc[36]),
            NestedField(38, "glacier_percent", DoubleType(), required=False, doc=desc[37]),
            NestedField(39, "lat", DoubleType(), required=False, doc=desc[38]),
            NestedField(40, "lon", DoubleType(), required=False, doc=desc[39]),
            NestedField(41, "geometry", BinaryType(), required=False, doc=desc[40]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the divides table
        """
        return pa.schema(
            [
                pa.field("div_id", pa.int64(), nullable=False),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("type", pa.string(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
                pa.field("bexp_mode", pa.float64(), nullable=True),
                pa.field("isltyp_mode", pa.float64(), nullable=True),
                pa.field("ivgtyp_mode", pa.float64(), nullable=True),
                pa.field("dksat_geomean", pa.float64(), nullable=True),
                pa.field("psisat_geomean", pa.float64(), nullable=True),
                pa.field("cwpvt_mean", pa.float64(), nullable=True),
                pa.field("mfsno_mean", pa.float64(), nullable=True),
                pa.field("refkdt_mean", pa.float64(), nullable=True),
                pa.field("mp_mean", pa.float64(), nullable=True),
                pa.field("quartz_mean", pa.float64(), nullable=True),
                pa.field("slope1km_mean", pa.float64(), nullable=True),
                pa.field("smcmax_mean", pa.float64(), nullable=True),
                pa.field("smcwlt_mean", pa.float64(), nullable=True),
                pa.field("vcmx_mean", pa.float64(), nullable=True),
                pa.field("imperv_mean", pa.float64(), nullable=True),
                pa.field("twi_q10", pa.float64(), nullable=True),
                pa.field("twi_q20", pa.float64(), nullable=True),
                pa.field("twi_q25", pa.float64(), nullable=True),
                pa.field("twi_q30", pa.float64(), nullable=True),
                pa.field("twi_q40", pa.float64(), nullable=True),
                pa.field("twi_q50", pa.float64(), nullable=True),
                pa.field("twi_q60", pa.float64(), nullable=True),
                pa.field("twi_q70", pa.float64(), nullable=True),
                pa.field("twi_q75", pa.float64(), nullable=True),
                pa.field("twi_q80", pa.float64(), nullable=True),
                pa.field("twi_q90", pa.float64(), nullable=True),
                pa.field("twi_q100", pa.float64(), nullable=True),
                pa.field("cgw", pa.float64(), nullable=True),
                pa.field("expon", pa.float64(), nullable=True),
                pa.field("max_gw_storage", pa.float64(), nullable=True),
                pa.field("elevation_mean", pa.float64(), nullable=True),
                pa.field("slope250m_mean", pa.float64(), nullable=True),
                pa.field("aspect_circmean", pa.float64(), nullable=True),
                pa.field("glacier_percent", pa.float64(), nullable=True),
                pa.field("lat", pa.float64(), nullable=True),
                pa.field("lon", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Flowpaths:
    """
    The schema for the flowpaths table

    Attributes
    ----------
    fp_id : int
        Unique flowpath identifier
    dn_nex_id : int
        Connected downstream nexus identifier
    up_nex_id : float
        Connected upstream nexus identifier
    div_id : int
        Associated divide identifier
    vpu_id : str
        Associated Vector Processing Unit (VPU) identifier
    length_km : float
        Flowpath length [in kilometers]
    area_sqkm : float
        Incremental areas of divide [in square kilometers]
    total_da_sqkm : float
        Total upstream drainage area [in square kilometers]
    mainstem_lp : int
        Associated flowpath mainstem (primary downstream segment)
    path_length : float
        Downstream path length (TODO - Get specification on this)
    dn_hydroseq : int
        Downstream hydrologic sequence
    hydroseq : int
        Hydrologic sequence
    stream_order : int
        Stream order of the mapped reference flowpath
    mean_elevation : float
        Terrain elevation
    slope : float
        Terrain slope
    n : float
        Manning's in channel roughness
    r : float
        Hydraulic radius
    y : float
        Estimated depth associated with top width
    ncc : float
        Compound channel top width
    btmwdth : float
        Bottom width of channel
    chslp : float
        Channel side slope
    musx : float
        Muskingum weighting factor
    musk : int
        Muskingum routing time
    topwdth : float
        Top width
    topwdthcc : float
        Compound channel top width
    topwdthcc_ml : float
        Compound channel top width at maximum levee
    topwdth_ml : float
        Top width at maximum levee
    y_ml : float
        Estimated depth associated with top width at maximum levee
    r_ml : float
        Hydraulic radius at maximum levee
    geometry : binary
        Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format

    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the flowpaths table
        """
        return [
            "fp_id",
            "dn_nex_id",
            "up_nex_id",
            "div_id",
            "vpu_id",
            "length_km",
            "area_sqkm",
            "total_da_sqkm",
            "mainstem_lp",
            "path_length",
            "dn_hydroseq",
            "hydroseq",
            "stream_order",
            "mean_elevation",
            "slope",
            "n",
            "r",
            "y",
            "ncc",
            "btmwdth",
            "chslp",
            "musx",
            "musk",
            "topwdth",
            "topwdthcc",
            "topwdthcc_ml",
            "topwdth_ml",
            "y_ml",
            "r_ml",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the flowpaths table
        """
        desc = [
            "Unique flowpath identifier",
            "Connected downstream nexus identifier",
            "Connected upstream nexus identifier",
            "Associated divide identifier",
            "Associated Vector Processing Unit (VPU) identifier",
            "Flowpath length [in kilometers]",
            "Incremental areas of divide [in square kilometers]",
            "Total upstream drainage area [in square kilometers]",
            "Associated flowpath mainstem (primary downstream segment)",
            "Downstream path length (TODO - Get specification on this)",
            "Downstream hydrologic sequence",
            "Hydrologic sequence",
            "Stream order of the mapped reference flowpath",
            "Terrain elevation",
            "Terrain slope",
            "Manning's in channel roughness",
            "Hydraulic radius",
            "Estimated depth associated with top width",
            "Compound channel top width",
            "Bottom width of channel",
            "Channel side slope",
            "Muskingum weighting factor",
            "Muskingum routing time",
            "Top width",
            "Compound channel top width",
            "Compound channel top width at maximum levee",
            "Top width at maximum levee",
            "Estimated depth associated with top width at maximum levee",
            "Hydraulic radius at maximum levee",
            "Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "fp_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_nex_id", LongType(), required=False, doc=desc[1]),
            NestedField(3, "up_nex_id", DoubleType(), required=False, doc=desc[2]),
            NestedField(4, "div_id", LongType(), required=False, doc=desc[3]),
            NestedField(5, "vpu_id", StringType(), required=False, doc=desc[4]),
            NestedField(6, "length_km", DoubleType(), required=False, doc=desc[5]),
            NestedField(7, "area_sqkm", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "total_da_sqkm", DoubleType(), required=False, doc=desc[7]),
            NestedField(9, "mainstem_lp", LongType(), required=False, doc=desc[8]),
            NestedField(10, "path_length", DoubleType(), required=False, doc=desc[9]),
            NestedField(11, "dn_hydroseq", LongType(), required=False, doc=desc[10]),
            NestedField(12, "hydroseq", LongType(), required=False, doc=desc[11]),
            NestedField(13, "stream_order", LongType(), required=False, doc=desc[12]),
            NestedField(14, "mean_elevation", DoubleType(), required=False, doc=desc[13]),
            NestedField(15, "slope", DoubleType(), required=False, doc=desc[14]),
            NestedField(16, "n", DoubleType(), required=False, doc=desc[15]),
            NestedField(17, "r", FloatType(), required=False, doc=desc[16]),
            NestedField(18, "y", FloatType(), required=False, doc=desc[17]),
            NestedField(19, "ncc", DoubleType(), required=False, doc=desc[18]),
            NestedField(20, "btmwdth", DoubleType(), required=False, doc=desc[19]),
            NestedField(21, "chslp", DoubleType(), required=False, doc=desc[20]),
            NestedField(22, "musx", DoubleType(), required=False, doc=desc[21]),
            NestedField(23, "musk", LongType(), required=False, doc=desc[22]),
            NestedField(24, "topwdth", DoubleType(), required=False, doc=desc[23]),
            NestedField(25, "topwdthcc", DoubleType(), required=False, doc=desc[24]),
            NestedField(26, "topwdthcc_ml", DoubleType(), required=False, doc=desc[25]),
            NestedField(27, "topwdth_ml", DoubleType(), required=False, doc=desc[26]),
            NestedField(28, "y_ml", FloatType(), required=False, doc=desc[27]),
            NestedField(29, "r_ml", FloatType(), required=False, doc=desc[28]),
            NestedField(30, "geometry", BinaryType(), required=False, doc=desc[29]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the flowpaths table
        """
        return pa.schema(
            [
                pa.field("fp_id", pa.int64(), nullable=False),
                pa.field("dn_nex_id", pa.int64(), nullable=True),
                pa.field("up_nex_id", pa.float64(), nullable=True),
                pa.field("div_id", pa.int64(), nullable=True),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("length_km", pa.float64(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
                pa.field("total_da_sqkm", pa.float64(), nullable=True),
                pa.field("mainstem_lp", pa.int64(), nullable=True),
                pa.field("path_length", pa.float64(), nullable=True),
                pa.field("dn_hydroseq", pa.int64(), nullable=True),
                pa.field("hydroseq", pa.int64(), nullable=True),
                pa.field("stream_order", pa.int64(), nullable=True),
                pa.field("mean_elevation", pa.float64(), nullable=True),
                pa.field("slope", pa.float64(), nullable=True),
                pa.field("n", pa.float64(), nullable=True),
                pa.field("r", pa.float32(), nullable=True),
                pa.field("y", pa.float32(), nullable=True),
                pa.field("ncc", pa.float64(), nullable=True),
                pa.field("btmwdth", pa.float64(), nullable=True),
                pa.field("chslp", pa.float64(), nullable=True),
                pa.field("musx", pa.float64(), nullable=True),
                pa.field("musk", pa.int64(), nullable=True),
                pa.field("topwdth", pa.float64(), nullable=True),
                pa.field("topwdthcc", pa.float64(), nullable=True),
                pa.field("topwdthcc_ml", pa.float64(), nullable=True),
                pa.field("topwdth_ml", pa.float64(), nullable=True),
                pa.field("y_ml", pa.float32(), nullable=True),
                pa.field("r_ml", pa.float32(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Nexus:
    """
    The schema for the nexus table

    Attributes
    ----------
    nex_id : int
        Unique nexus identifier
    dn_fp_id : float
        Associated downstream flowpath identifier
    vpu_id : str
        Vector Processing Unit identifier
    geometry : binary
        Spatial Geometry (POINT format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the nexus table
        """
        return [
            "nex_id",
            "dn_fp_id",
            "vpu_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the nexus table
        """
        desc = [
            "Unique nexus identifier",
            "Associated downstream flowpath identifier",
            "Vector Processing Unit identifier",
            "Spatial Geometry (POINT format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "nex_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_fp_id", DoubleType(), required=False, doc=desc[1]),
            NestedField(3, "vpu_id", StringType(), required=False, doc=desc[2]),
            NestedField(4, "geometry", BinaryType(), required=False, doc=desc[3]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the nexus table
        """
        return pa.schema(
            [
                pa.field("nex_id", pa.int64(), nullable=False),
                pa.field("dn_fp_id", pa.float64(), nullable=True),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class ReferenceFlowpaths:
    """
    The schema for the reference_flowpaths table

    Attributes
    ----------
    ref_fp_id : int
        A flowpath ID from the full, reference hydrofabric dataset
    fp_id : float
        A flowpath ID from the flowpath table that was derived from the reference flowpath ID
    virtual_fp_id : int
        Virtual flowpath identifier
    div_id : int
        Associated divide identifier
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the reference_flowpaths table
        """
        return [
            "ref_fp_id",
            "fp_id",
            "virtual_fp_id",
            "div_id",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the reference_flowpaths table
        """
        desc = [
            "A flowpath ID from the full, reference hydrofabric dataset",
            "A flowpath ID from the flowpath table that was derived from the reference flowpath ID",
            "Virtual flowpath identifier",
            "Associated divide identifier",
        ]
        return Schema(
            NestedField(1, "ref_fp_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "fp_id", LongType(), required=False, doc=desc[1]),
            NestedField(3, "virtual_fp_id", LongType(), required=False, doc=desc[2]),
            NestedField(4, "div_id", LongType(), required=False, doc=desc[3]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the reference_flowpaths table
        """
        return pa.schema(
            [
                pa.field("ref_fp_id", pa.int64(), nullable=False),
                pa.field("fp_id", pa.int64(), nullable=True),
                pa.field("virtual_fp_id", pa.int64(), nullable=True),
                pa.field("div_id", pa.int64(), nullable=True),
            ]
        )


class Waterbodies:
    """
    The schema for the waterbodies table

    Attributes
    ----------
    wb_id : int
        Unique waterbody identifier
    fp_id : float
        Associated flowpath identifier
    hy_id : int
        Hydrolocation identifier
    ref_fp_id : float
        Reference flowpath identifier
    dam_id : str
        Dam identifier
    dam_name : str
        Dam name
    dam_type : str
        Dam type
    LkArea : float
        Lake area
    LkMxE : float
        Lake maximum elevation
    WeirC : float
        Weir coefficient
    WeirL : float
        Weir length
    WeirE : float
        Weir elevation
    OrficeC : float
        Orifice coefficient
    OrficeA : float
        Orifice area
    OrficeE : float
        Orifice elevation
    Dam_Length : float
        Dam length
    ifd : float
        Initial flood depth
    geometry : binary
        Spatial Geometry (POINT format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the waterbodies table
        """
        return [
            "wb_id",
            "fp_id",
            "hy_id",
            "ref_fp_id",
            "dam_id",
            "dam_name",
            "dam_type",
            "LkArea",
            "LkMxE",
            "WeirC",
            "WeirL",
            "WeirE",
            "OrficeC",
            "OrficeA",
            "OrficeE",
            "Dam_Length",
            "ifd",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the waterbodies table
        """
        desc = [
            "Unique waterbody identifier",
            "Associated flowpath identifier",
            "Hydrolocation identifier",
            "Reference flowpath identifier",
            "Dam identifier",
            "Dam name",
            "Dam type",
            "Lake area",
            "Lake maximum elevation",
            "Weir coefficient",
            "Weir length",
            "Weir elevation",
            "Orifice coefficient",
            "Orifice area",
            "Orifice elevation",
            "Dam length",
            "Initial flood depth",
            "Spatial Geometry (POLYGON format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "wb_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "fp_id", DoubleType(), required=False, doc=desc[1]),
            NestedField(3, "hy_id", LongType(), required=False, doc=desc[2]),
            NestedField(4, "ref_fp_id", DoubleType(), required=False, doc=desc[3]),
            NestedField(5, "dam_id", StringType(), required=False, doc=desc[4]),
            NestedField(6, "dam_name", StringType(), required=False, doc=desc[5]),
            NestedField(7, "dam_type", StringType(), required=False, doc=desc[6]),
            NestedField(8, "LkArea", FloatType(), required=False, doc=desc[7]),
            NestedField(9, "LkMxE", FloatType(), required=False, doc=desc[8]),
            NestedField(10, "WeirC", FloatType(), required=False, doc=desc[9]),
            NestedField(11, "WeirL", FloatType(), required=False, doc=desc[10]),
            NestedField(12, "WeirE", FloatType(), required=False, doc=desc[11]),
            NestedField(13, "OrficeC", FloatType(), required=False, doc=desc[12]),
            NestedField(14, "OrficeA", FloatType(), required=False, doc=desc[13]),
            NestedField(15, "OrficeE", FloatType(), required=False, doc=desc[14]),
            NestedField(16, "Dam_Length", FloatType(), required=False, doc=desc[15]),
            NestedField(17, "ifd", FloatType(), required=False, doc=desc[16]),
            NestedField(18, "geometry", BinaryType(), required=False, doc=desc[17]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the waterbodies table
        """
        return pa.schema(
            [
                pa.field("wb_id", pa.int64(), nullable=False),
                pa.field("fp_id", pa.float64(), nullable=True),
                pa.field("hy_id", pa.int64(), nullable=True),
                pa.field("ref_fp_id", pa.float64(), nullable=True),
                pa.field("dam_id", pa.string(), nullable=True),
                pa.field("dam_name", pa.string(), nullable=True),
                pa.field("dam_type", pa.string(), nullable=True),
                pa.field("LkArea", pa.float32(), nullable=True),
                pa.field("LkMxE", pa.float32(), nullable=True),
                pa.field("WeirC", pa.float32(), nullable=True),
                pa.field("WeirL", pa.float32(), nullable=True),
                pa.field("WeirE", pa.float32(), nullable=True),
                pa.field("OrficeC", pa.float32(), nullable=True),
                pa.field("OrficeA", pa.float32(), nullable=True),
                pa.field("OrficeE", pa.float32(), nullable=True),
                pa.field("Dam_Length", pa.float32(), nullable=True),
                pa.field("ifd", pa.float32(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Gages:
    """
    The schema for the gages table

    Attributes
    ----------
    site_no : str
        USGS Site Number
    status : str
        Gage Status
    hy_id : int
        Hydrolocation Identifier
    USGS_basin_km2 : float
        USGS Basin Area in square kilometers
    ref_fp_id : float
        Reference Flowpath Identifier
    method_fp_to_gage : str
        Method used to associate flowpath to gage
    fp_id : float
        Flowpath Identifier
    virtual_fp_id : float
        Virtual Flowpath Identifier
    geometry : binary
        Spatial Geometry (POINT format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the gages table
        """
        return [
            "site_no",
            "status",
            "hy_id",
            "USGS_basin_km2",
            "ref_fp_id",
            "method_fp_to_gage",
            "fp_id",
            "virtual_fp_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the gages table
        """
        desc = [
            "USGS Site Number",
            "Gage Status",
            "Hydrolocation Identifier",
            "USGS Basin Area in square kilometers",
            "Reference Flowpath Identifier",
            "Method used to associate flowpath to gage",
            "Flowpath Identifier",
            "Virtual Flowpath Identifier",
            "Spatial Geometry (POINT format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "site_no", StringType(), required=True, doc=desc[0]),
            NestedField(2, "status", StringType(), required=False, doc=desc[1]),
            NestedField(3, "hy_id", LongType(), required=False, doc=desc[2]),
            NestedField(4, "USGS_basin_km2", DoubleType(), required=False, doc=desc[3]),
            NestedField(5, "ref_fp_id", DoubleType(), required=False, doc=desc[4]),
            NestedField(6, "method_fp_to_gage", StringType(), required=False, doc=desc[5]),
            NestedField(7, "fp_id", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "virtual_fp_id", DoubleType(), required=False, doc=desc[7]),
            NestedField(9, "geometry", BinaryType(), required=False, doc=desc[8]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the gages table
        """
        return pa.schema(
            [
                pa.field("site_no", pa.string(), nullable=False),
                pa.field("status", pa.string(), nullable=True),
                pa.field("hy_id", pa.int64(), nullable=True),
                pa.field("USGS_basin_km2", pa.float64(), nullable=True),
                pa.field("ref_fp_id", pa.float64(), nullable=True),
                pa.field("method_fp_to_gage", pa.string(), nullable=True),
                pa.field("fp_id", pa.float64(), nullable=True),
                pa.field("virtual_fp_id", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class VirtualFlowpaths:
    """
    The schema for the virtual_flowpaths table

    Attributes
    ----------
    virtual_fp_id : int
        Virtual flowpath identifier
    dn_virtual_nex_id : int
        Downstream virtual nexus identifier
    up_virtual_nex_id : float
        Upstream virtual nexus identifier
    routing_segment : bool
        Routing segment indicator
    length_km : float
        Flowpath length [in kilometers]
    area_sqkm : float
        Incremental areas of divide [in square kilometers]
    percentage_area_contribution : float
        Percentage area contribution
    vpu_id : str
        Vector Processing Unit identifier
    geometry : binary
        Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the virtual_flowpaths table
        """
        return [
            "virtual_fp_id",
            "dn_virtual_nex_id",
            "up_virtual_nex_id",
            "routing_segment",
            "length_km",
            "area_sqkm",
            "percentage_area_contribution",
            "vpu_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the virtual_flowpaths table
        """
        desc = [
            "Virtual flowpath identifier",
            "Downstream virtual nexus identifier",
            "Upstream virtual nexus identifier",
            "Routing segment indicator",
            "Flowpath length [in kilometers]",
            "Incremental areas of divide [in square kilometers]",
            "Percentage area contribution",
            "Vector Processing Unit identifier",
            "Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "virtual_fp_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_virtual_nex_id", LongType(), required=False, doc=desc[1]),
            NestedField(3, "up_virtual_nex_id", DoubleType(), required=False, doc=desc[2]),
            NestedField(4, "routing_segment", BooleanType(), required=False, doc=desc[3]),
            NestedField(5, "length_km", DoubleType(), required=False, doc=desc[4]),
            NestedField(6, "area_sqkm", DoubleType(), required=False, doc=desc[5]),
            NestedField(7, "percentage_area_contribution", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "vpu_id", StringType(), required=False, doc=desc[7]),
            NestedField(9, "geometry", BinaryType(), required=False, doc=desc[8]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the virtual_flowpaths table
        """
        return pa.schema(
            [
                pa.field("virtual_fp_id", pa.int64(), nullable=False),
                pa.field("dn_virtual_nex_id", pa.int64(), nullable=True),
                pa.field("up_virtual_nex_id", pa.float64(), nullable=True),
                pa.field("routing_segment", pa.bool_(), nullable=True),
                pa.field("length_km", pa.float64(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
                pa.field("percentage_area_contribution", pa.float64(), nullable=True),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class VirtualNexus:
    """
    The schema for the virtual_nexus table

    Attributes
    ----------
    virtual_nex_id : int
        Virtual nexus identifier
    dn_virtual_fp_id : float
        Downstream virtual flowpath identifier
    vpu_id : str
        Vector Processing Unit identifier
    geometry : binary
        Spatial Geometry (POINT format) - stored in WKB binary format
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the virtual_nexus table
        """
        return [
            "virtual_nex_id",
            "dn_virtual_fp_id",
            "vpu_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the virtual_nexus table
        """
        desc = [
            "Virtual nexus identifier",
            "Downstream virtual flowpath identifier",
            "Vector Processing Unit identifier",
            "Spatial Geometry (POINT format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "virtual_nex_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_virtual_fp_id", DoubleType(), required=False, doc=desc[1]),
            NestedField(3, "vpu_id", StringType(), required=False, doc=desc[2]),
            NestedField(4, "geometry", BinaryType(), required=False, doc=desc[3]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the virtual_nexus table
        """
        return pa.schema(
            [
                pa.field("virtual_nex_id", pa.int64(), nullable=False),
                pa.field("dn_virtual_fp_id", pa.float64(), nullable=True),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class NHD:
    """
    The schema for the NHD crosswalk table

    Attributes
    ----------
    reach_id : int
        NHD COMID/Feature Reach identifier
    fp_id : int
        Flowpath Identifier
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the NHD crosswalk table
        """
        return [
            "reach_id",
            "fp_id",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the NHD crosswalk table
        """
        desc = [
            "NHD COMID/Feature Reach identifier",
            "Flowpath Identifier",
        ]
        return Schema(
            NestedField(1, "reach_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "fp_id", LongType(), required=False, doc=desc[1]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the NHD crosswalk table
        """
        return pa.schema(
            [
                pa.field("reach_id", pa.int64(), nullable=False),
                pa.field("fp_id", pa.int64(), nullable=True),
            ]
        )


class Hydrolocations:
    """
    The schema for the virtual_nexus table

    Attributes
    ----------
    hy_id : int
        Hydrolocations identifier
    dn_nex_id : int
        Downstream nexus identifier
    """

    @classmethod
    def columns(cls) -> list[str]:
        """
        Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns for the hydrolocations table
        """
        return [
            "hy_id",
            "dn_nex_id",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """
        Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for the hydrolocations table
        """
        desc = [
            "Hydrolocations identifier",
            "Downstream nexus identifier",
        ]
        return Schema(
            NestedField(1, "hy_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_nex_id", LongType(), required=False, doc=desc[1]),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """
        Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for the hydrolocations table
        """
        return pa.schema(
            [
                pa.field("hy_id", pa.int64(), nullable=False),
                pa.field("dn_nex_id", pa.int64(), nullable=True),
            ]
        )
