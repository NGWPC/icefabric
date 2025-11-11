"""
Contains the PyIceberg Table schemas for the updated Hydrofabric v2.2 data model tables

NOTE - THIS IS A WORK IN PROGRESS
"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, DoubleType, IntegerType, NestedField, StringType


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
            "Spatial Geometry (MULTIPOLYGON format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "div_id", StringType(), required=True, doc=desc[0]),
            NestedField(2, "vpu_id", StringType(), required=False, doc=desc[1]),
            NestedField(3, "type", StringType(), required=False, doc=desc[2]),
            NestedField(4, "area_sqkm", DoubleType(), required=False, doc=desc[3]),
            NestedField(5, "geometry", BinaryType(), required=False, doc=desc[4]),
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
                pa.field("vpu_id", pa.string(), nullable=False),
                pa.field("div_id", pa.string(), nullable=True),
                pa.field("type", pa.string(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
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
            "Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format",
        ]
        return Schema(
            NestedField(1, "fp_id", StringType(), required=True, doc=desc[0]),
            NestedField(2, "dn_nex_id", StringType(), required=False, doc=desc[1]),
            NestedField(3, "up_nex_id", StringType(), required=False, doc=desc[2]),
            NestedField(4, "div_id", StringType(), required=False, doc=desc[3]),
            NestedField(5, "vpu_id", StringType(), required=False, doc=desc[4]),
            NestedField(6, "hydroseq", IntegerType(), required=False, doc=desc[5]),
            NestedField(7, "length_km", DoubleType(), required=False, doc=desc[6]),
            NestedField(8, "area_sqkm", DoubleType(), required=False, doc=desc[7]),
            NestedField(9, "total_da_sqkm", DoubleType(), required=False, doc=desc[8]),
            NestedField(10, "mainstem_lp", IntegerType(), required=False, doc=desc[9]),
            NestedField(11, "path_length", DoubleType(), required=False, doc=desc[10]),
            NestedField(12, "dn_hydroseq", IntegerType(), required=False, doc=desc[11]),
            NestedField(13, "streamorder", IntegerType(), required=False, doc=desc[12]),
            NestedField(14, "geometry", BinaryType(), required=False, doc=desc[13]),
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
                pa.field("fp_id", pa.string(), nullable=False),
                pa.field("dn_nex_id", pa.string(), nullable=True),
                pa.field("up_nex_id", pa.string(), nullable=True),
                pa.field("div_id", pa.string(), nullable=True),
                pa.field("vpu_id", pa.string(), nullable=True),
                pa.field("hydroseq", pa.int64(), nullable=True),
                pa.field("length_km", pa.float64(), nullable=True),
                pa.field("area_sqkm", pa.float64(), nullable=True),
                pa.field("total_da_sqkm", pa.float64(), nullable=True),
                pa.field("mainstem_lp", pa.int64(), nullable=True),
                pa.field("path_length", pa.float64(), nullable=True),
                pa.field("dn_hydroseq", pa.int64(), nullable=True),
                pa.field("streamorder", pa.int64(), nullable=True),
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
            NestedField(1, "nex_id", StringType(), required=True, doc=desc[0]),
            NestedField(2, "dn_fp_id", StringType(), required=False, doc=desc[1]),
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
                pa.field("nex_id", pa.string(), nullable=False),
                pa.field("dn_fp_id", pa.string(), nullable=True),
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
