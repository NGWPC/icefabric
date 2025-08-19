"""Contains the PyIceberg Table schema for the conus reference fabric"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, BooleanType, DoubleType, NestedField, StringType


class ReferenceFlowpaths:
    """The schema for the reference_flowpaths table containing flowpath data"""

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "flowpath_id",
            "VPUID",
            "reachcode",
            "frommeas",
            "tomeas",
            "burnline_event",
            "reversed",
            "source",
            "flowpath_toid",
            "lengthkm",
            "areasqkm",
            "totdasqkm",
            "terminalpa",
            "dnhydroseq",
            "hydroseq",
            "mainstemlp",
            "dnlevelpat",
            "pathlength",
            "terminalfl",
            "streamorder",
            "startflag",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for reference_flowpaths
        """
        return Schema(
            NestedField(1, "flowpath_id", StringType(), required=True),
            NestedField(2, "VPUID", StringType(), required=False),
            NestedField(3, "reachcode", StringType(), required=False),
            NestedField(4, "frommeas", DoubleType(), required=False),
            NestedField(5, "tomeas", DoubleType(), required=False),
            NestedField(6, "burnline_event", BooleanType(), required=False),
            NestedField(7, "reversed", BooleanType(), required=False),
            NestedField(8, "source", StringType(), required=False),
            NestedField(9, "flowpath_toid", DoubleType(), required=False),
            NestedField(10, "lengthkm", DoubleType(), required=False),
            NestedField(11, "areasqkm", DoubleType(), required=False),
            NestedField(12, "totdasqkm", DoubleType(), required=False),
            NestedField(13, "terminalpa", DoubleType(), required=False),
            NestedField(14, "dnhydroseq", DoubleType(), required=False),
            NestedField(15, "hydroseq", DoubleType(), required=False),
            NestedField(16, "mainstemlp", DoubleType(), required=False),
            NestedField(17, "dnlevelpat", DoubleType(), required=False),
            NestedField(18, "pathlength", DoubleType(), required=False),
            NestedField(19, "terminalfl", DoubleType(), required=False),
            NestedField(20, "streamorder", DoubleType(), required=False),
            NestedField(21, "startflag", DoubleType(), required=False),
            NestedField(22, "geometry", BinaryType(), required=False),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for reference_flowpaths
        """
        return pa.schema(
            [
                pa.field("flowpath_id", pa.string(), nullable=False),
                pa.field("VPUID", pa.string(), nullable=True),
                pa.field("reachcode", pa.string(), nullable=True),
                pa.field("frommeas", pa.float64(), nullable=True),
                pa.field("tomeas", pa.float64(), nullable=True),
                pa.field("burnline_event", pa.bool_(), nullable=True),
                pa.field("reversed", pa.bool_(), nullable=True),
                pa.field("source", pa.string(), nullable=True),
                pa.field("flowpath_toid", pa.float64(), nullable=True),
                pa.field("lengthkm", pa.float64(), nullable=True),
                pa.field("areasqkm", pa.float64(), nullable=True),
                pa.field("totdasqkm", pa.float64(), nullable=True),
                pa.field("terminalpa", pa.float64(), nullable=True),
                pa.field("dnhydroseq", pa.float64(), nullable=True),
                pa.field("hydroseq", pa.float64(), nullable=True),
                pa.field("mainstemlp", pa.float64(), nullable=True),
                pa.field("dnlevelpat", pa.float64(), nullable=True),
                pa.field("pathlength", pa.float64(), nullable=True),
                pa.field("terminalfl", pa.float64(), nullable=True),
                pa.field("streamorder", pa.float64(), nullable=True),
                pa.field("startflag", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class ReferenceDivides:
    """The schema for the reference_flowpaths table containing flowpath data"""

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "divide_id",
            "vpuid",
            "areasqkm",
            "has_flowpath",
            "flowpath_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for reference_flowpaths
        """
        return Schema(
            NestedField(1, "divide_id", StringType(), required=True),
            NestedField(2, "vpuid", StringType(), required=False),
            NestedField(3, "areasqkm", DoubleType(), required=False),
            NestedField(4, "has_flowpath", DoubleType(), required=False),
            NestedField(5, "flowpath_id", StringType(), required=False),
            NestedField(6, "geometry", BinaryType(), required=False),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for reference_flowpaths
        """
        return pa.schema(
            [
                pa.field("divide_id", pa.string(), nullable=False),
                pa.field("vpuid", pa.string(), nullable=True),
                pa.field("areasqkm", pa.float64(), nullable=True),
                pa.field("has_flowpath", pa.float64(), nullable=True),
                pa.field("flowpath_id", pa.string(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )
