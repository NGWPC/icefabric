"""
Contains the PyIceberg Table schemas for the updated Hydrofabric v2.2 data model tables

NOTE - THIS IS A WORK IN PROGRESS
"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, DoubleType, FloatType, LongType, NestedField, StringType


class Divides:
    """
    The schema for the divides table

    Attributes
    ----------
    div_id : str
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
    psisat_geommean : float
        Saturated capillary head
    cwpvt_mean : float
        Empirical canopy wind parameter
    msfno_mean : float
        Melt factor for snow depletion curve
    refkdt_mean : float
        Reference soil infiltration parameter
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
    twi_q25 : float
        Topographic wetness index 1st quartile
    twi_q50 : float
        Topographic wetness index 2nd quartile
    twi_q75 : float
        Topographic wetness index 3rd quartile
    twi_q100 : float
        Topographic wetness index 4th quartile
    elevation_mean : float
        Terrain elevation
    slope250m_mean : float
        Terrain slope
    aspect_circmean : float
        Terrain aspect
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
            "psisat_geommean",
            "cwpvt_mean",
            "msfno_mean",
            "refkdt_mean",
            "slope1km_mean",
            "smcmax_mean",
            "smcwlt_mean",
            "vcmx_mean",
            "imperv_mean",
            "twi_q25",
            "twi_q50",
            "twi_q75",
            "twi_q100",
            "elevation_mean",
            "slope250m_mean",
            "aspect_circmean",
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
            "modifies the gradient of the hydraulic head at the soil bottom",
            "Saturated soil moisture content",
            "Wilting point soil moisture content",
            "Maximum rate of carboxylation at 25 C",
            "Percentage of catchment with an impervious surface",
            "Topographic wetness index 1st quartile",
            "Topographic wetness index 2nd quartile",
            "Topographic wetness index 3rd quartile",
            "Topographic wetness index 4th quartile",
            "Terrain elevation",
            "Terrain slope",
            "Terrain aspect",
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
            NestedField(9, "psisat_geommean", DoubleType(), required=False, doc=desc[8]),
            NestedField(10, "cwpvt_mean", DoubleType(), required=False, doc=desc[9]),
            NestedField(11, "msfno_mean", DoubleType(), required=False, doc=desc[10]),
            NestedField(12, "refkdt_mean", DoubleType(), required=False, doc=desc[11]),
            NestedField(13, "slope1km_mean", DoubleType(), required=False, doc=desc[12]),
            NestedField(14, "smcmax_mean", DoubleType(), required=False, doc=desc[13]),
            NestedField(15, "smcwlt_mean", DoubleType(), required=False, doc=desc[14]),
            NestedField(16, "vcmx_mean", DoubleType(), required=False, doc=desc[15]),
            NestedField(17, "imperv_mean", DoubleType(), required=False, doc=desc[16]),
            NestedField(18, "twi_q25", DoubleType(), required=False, doc=desc[17]),
            NestedField(19, "twi_q50", DoubleType(), required=False, doc=desc[18]),
            NestedField(20, "twi_q75", DoubleType(), required=False, doc=desc[19]),
            NestedField(21, "twi_q100", DoubleType(), required=False, doc=desc[20]),
            NestedField(22, "elevation_mean", DoubleType(), required=False, doc=desc[21]),
            NestedField(23, "slope250m_mean", DoubleType(), required=False, doc=desc[22]),
            NestedField(24, "aspect_circmean", DoubleType(), required=False, doc=desc[23]),
            NestedField(25, "geometry", BinaryType(), required=False, doc=desc[24]),
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
                pa.field("psisat_geommean", pa.float64(), nullable=True),
                pa.field("cwpvt_mean", pa.float64(), nullable=True),
                pa.field("msfno_mean", pa.float64(), nullable=True),
                pa.field("refkdt_mean", pa.float64(), nullable=True),
                pa.field("slope1km_mean", pa.float64(), nullable=True),
                pa.field("smcmax_mean", pa.float64(), nullable=True),
                pa.field("smcwlt_mean", pa.float64(), nullable=True),
                pa.field("vcmx_mean", pa.float64(), nullable=True),
                pa.field("imperv_mean", pa.float64(), nullable=True),
                pa.field("twi_q25", pa.float64(), nullable=True),
                pa.field("twi_q50", pa.float64(), nullable=True),
                pa.field("twi_q75", pa.float64(), nullable=True),
                pa.field("twi_q100", pa.float64(), nullable=True),
                pa.field("elevation_mean", pa.float64(), nullable=True),
                pa.field("slope250m_mean", pa.float64(), nullable=True),
                pa.field("aspect_circmean", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Flowpaths:
    """
    The schema for the flowpaths table

    Attributes
    ----------
    fp_id : str
        Unique flowpath identifier
    dn_nex_id : str
        Connected downstream nexus identifier
    up_nex_id : str
        Connected upstream nexus identifier
    div_id : str
        Associated divide identifier
    vpu_id : str
        Associated Vector Processing Unit (VPU) identifier
    hydroseq : int
        Hydrologic sequence
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
    streamorder : int
        Stream order of the mapped reference flowpath
    mean_elevation : float
        Terrain elevation
    slope : float
        Terrain slope
    n : float
        Manning's in channel roughness
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
    topwdthcc : float
        Compound channel top width
    topwdth : float
        Top width
    y : float
        Estimated depth associated with top width
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
            "hydroseq",
            "length_km",
            "area_sqkm",
            "total_da_sqkm",
            "mainstem_lp",
            "path_length",
            "dn_hydroseq",
            "streamorder",
            "mean_elevation",
            "slope",
            "n",
            "ncc",
            "btmwdth",
            "chslp",
            "musx",
            "musk",
            "topwdthcc",
            "topwdth",
            "y",
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
            "Hydrologic sequence",
            "Flowpath length [in kilometers]",
            "Incremental areas of divide [in square kilometers]",
            "Total upstream drainage area [in square kilometers]",
            "Associated flowpath mainstem (primary downstream segment)",
            "Downstream path length (TODO - Get specification on this)",
            "Downstream hydrologic sequence",
            "Stream order of the mapped reference flowpath",
            "Terrain elevation",
            "Terrain slope",
            "Manning's in channel roughness",
            "Compound channel top width",
            "Bottom width of channel",
            "Channel side slope",
            "Muskingum weighting factor",
            "Muskingum routing time",
            "Compound channel top width",
            "Top width",
            "Estimated depth associated with top width",
            "Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "fp_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_nex_id", LongType(), required=False, doc=desc[1]),
            NestedField(3, "up_nex_id", DoubleType(), required=False, doc=desc[2]),
            NestedField(4, "div_id", LongType(), required=False, doc=desc[3]),
            NestedField(5, "vpu_id", StringType(), required=False, doc=desc[4]),
            NestedField(6, "hydroseq", LongType(), required=False, doc=desc[5]),
            NestedField(7, "length_km", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "area_sqkm", DoubleType(), required=False, doc=desc[7]),
            NestedField(9, "total_da_sqkm", DoubleType(), required=False, doc=desc[8]),
            NestedField(10, "mainstem_lp", LongType(), required=False, doc=desc[9]),
            NestedField(11, "path_length", DoubleType(), required=False, doc=desc[10]),
            NestedField(12, "dn_hydroseq", LongType(), required=False, doc=desc[11]),
            NestedField(13, "streamorder", LongType(), required=False, doc=desc[12]),
            NestedField(14, "mean_elevation", DoubleType(), required=False, doc=desc[13]),
            NestedField(15, "slope", DoubleType(), required=False, doc=desc[14]),
            NestedField(16, "n", DoubleType(), required=False, doc=desc[15]),
            NestedField(17, "ncc", DoubleType(), required=False, doc=desc[16]),
            NestedField(18, "btmwdth", DoubleType(), required=False, doc=desc[17]),
            NestedField(19, "chslp", DoubleType(), required=False, doc=desc[18]),
            NestedField(20, "musx", DoubleType(), required=False, doc=desc[19]),
            NestedField(21, "musk", LongType(), required=False, doc=desc[20]),
            NestedField(22, "topwdthcc", DoubleType(), required=False, doc=desc[21]),
            NestedField(23, "topwdth", FloatType(), required=False, doc=desc[22]),
            NestedField(24, "y", FloatType(), required=False, doc=desc[23]),
            NestedField(25, "geometry", BinaryType(), required=False, doc=desc[24]),
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
                pa.field("hydroseq", pa.int64(), nullable=True),
                pa.field("length_km", pa.float64(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
                pa.field("total_da_sqkm", pa.float64(), nullable=True),
                pa.field("mainstem_lp", pa.int64(), nullable=True),
                pa.field("path_length", pa.float64(), nullable=True),
                pa.field("dn_hydroseq", pa.int64(), nullable=True),
                pa.field("streamorder", pa.int64(), nullable=True),
                pa.field("mean_elevation", pa.float64(), nullable=True),
                pa.field("slope", pa.float64(), nullable=True),
                pa.field("n", pa.float64(), nullable=True),
                pa.field("ncc", pa.float64(), nullable=True),
                pa.field("btmwdth", pa.float64(), nullable=True),
                pa.field("chslp", pa.float64(), nullable=True),
                pa.field("musx", pa.float64(), nullable=True),
                pa.field("musk", pa.int64(), nullable=True),
                pa.field("topwdthcc", pa.float64(), nullable=True),
                pa.field("topwdth", pa.float32(), nullable=True),
                pa.field("y", pa.float32(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Nexus:
    """
    The schema for the nexus table

    Attributes
    ----------
    nex_id : str
        Unique nexus identifier
    dn_fp_id : str
        Associated downstream flowpath identifier
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
            "Spatial Geometry (POINT format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "nex_id", LongType(), required=True, doc=desc[0]),
            NestedField(2, "dn_fp_id", DoubleType(), required=False, doc=desc[1]),
            NestedField(3, "geometry", BinaryType(), required=False, doc=desc[2]),
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
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class ReferenceFlowpaths:
    """
    The schema for the reference_flowpaths table

    Attributes
    ----------
    ref_fp_id : str
        A flowpath ID from the full, reference hydrofabric dataset
    fp_id : str
        A flowpath ID from the flowpath table that was derived from the reference flowpath ID

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
        ]
        return Schema(
            NestedField(1, "ref_fp_id", StringType(), required=True, doc=desc[0]),
            NestedField(2, "fp_id", StringType(), required=True, doc=desc[1]),
            identifier_field_ids=[1, 2],
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
                pa.field("ref_fp_id", pa.string(), nullable=False),
                pa.field("fp_id", pa.string(), nullable=False),
            ]
        )
