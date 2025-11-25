"""Contains the PyIceberg Table schema for all hydrofabric layers"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType


class NHFSnapshot:
    """The schema containing all snapshots of the layers for the NHF. This is used to version control many layers

    Attributes
    ----------
    - divides
    - flowpaths
    - nexus
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
            "domain"
            "divides",
            "flowpaths",
            "nexus"
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
            NestedField(2, "divides", LongType(), required=False),
            NestedField(3, "flowpaths", LongType(), required=False),
            NestedField(4, "nexus", LongType(), required=False),
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
                pa.field("divides", pa.int64(), nullable=True),
                pa.field("flowpaths", pa.int64(), nullable=True),
                pa.field("nexus", pa.int64(), nullable=True),
            ]
        )
