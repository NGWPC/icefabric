"""Contains the PyIceberg Table schema for all hydrofabric layers"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType


class HydrofabricSnapshot:
    """The schema containing all snapshots of the layers for the Hydrofabric. This is used to version control many layers

    Attributes
    ----------
    - domain
    - divide-attributes
    - divides
    - flowpath-attributes
    - flowpath-attributes-ml
    - flowpaths
    - hydrolocations
    - lakes
    - network
    - nexus
    - pois
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "domain",
            "divide-attributes",
            "divides",
            "flowpath-attributes",
            "flowpath-attributes-ml",
            "flowpaths",
            "hydrolocations",
            "lakes",
            "network",
            "nexus",
            "pois",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for Hydrofabric
        """
        return Schema(
            NestedField(1, "domain", StringType(), required=True),
            NestedField(2, "divide-attributes", LongType(), required=False),
            NestedField(3, "divides", LongType(), required=False),
            NestedField(4, "flowpath-attributes", LongType(), required=False),
            NestedField(5, "flowpath-attributes-ml", LongType(), required=False),
            NestedField(6, "flowpaths", LongType(), required=False),
            NestedField(7, "hydrolocations", LongType(), required=False),
            NestedField(8, "lakes", LongType(), required=False),
            NestedField(9, "network", LongType(), required=False),
            NestedField(10, "nexus", LongType(), required=False),
            NestedField(11, "pois", LongType(), required=False),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for Hydrofabric
        """
        return pa.schema(
            [
                pa.field("domain", pa.string(), nullable=False),
                pa.field("divide-attributes", pa.int64(), nullable=True),
                pa.field("divides", pa.int64(), nullable=True),
                pa.field("flowpath-attributes", pa.int64(), nullable=True),
                pa.field("flowpath-attributes-ml", pa.int64(), nullable=True),
                pa.field("flowpaths", pa.int64(), nullable=True),
                pa.field("hydrolocations", pa.int64(), nullable=True),
                pa.field("lakes", pa.int64(), nullable=True),
                pa.field("network", pa.int64(), nullable=True),
                pa.field("nexus", pa.int64(), nullable=True),
                pa.field("pois", pa.int64(), nullable=True),
            ]
        )
