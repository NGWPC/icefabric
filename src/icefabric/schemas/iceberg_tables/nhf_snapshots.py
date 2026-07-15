"""Contains the PyIceberg Table schema for all hydrofabric layers"""

import pyarrow as pa
from pyiceberg.schema import Schema  # pyright: ignore[reportMissingImports]
from pyiceberg.types import LongType, NestedField


class NHFSnapshot:
    """The schema containing all snapshots of the layers for the NHF. This is used to version control many layers

    Attributes
    ----------
    - divides
    - flowpaths
    - nexus
    - reference_flowpaths
    - gages
    - virtual_flowpaths
    - virtual_nexus
    - hydrolocations
    - lakes
    - nhd
    - lakes_polygons
    - reservoir_da
    - lake_vfp_crosswalk
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
            "divides",
            "flowpaths",
            "nexus",
            "reference_flowpaths",
            "gages",
            "virtual_flowpaths",
            "virtual_nexus",
            "hydrolocations",
            "lakes",
            "nhd",
            "lakes_polygons",
            "reservoir_da",
            "lake_vfp_crosswalk",
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
            NestedField(1, "divides", LongType(), required=False),
            NestedField(2, "flowpaths", LongType(), required=False),
            NestedField(3, "nexus", LongType(), required=False),
            NestedField(4, "reference_flowpaths", LongType(), required=False),
            NestedField(5, "gages", LongType(), required=False),
            NestedField(6, "virtual_flowpaths", LongType(), required=False),
            NestedField(7, "virtual_nexus", LongType(), required=False),
            NestedField(8, "hydrolocations", LongType(), required=False),
            NestedField(9, "lakes", LongType(), required=False),
            NestedField(10, "nhd", LongType(), required=False),
            NestedField(11, "lakes_polygons", LongType(), required=False),
            NestedField(12, "reservoir_da", LongType(), required=False),
            NestedField(13, "lake_vfp_crosswalk", LongType(), required=False),
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
                pa.field("divides", pa.int64(), nullable=True),
                pa.field("flowpaths", pa.int64(), nullable=True),
                pa.field("nexus", pa.int64(), nullable=True),
                pa.field("reference_flowpaths", pa.int64(), nullable=True),
                pa.field("gages", pa.int64(), nullable=True),
                pa.field("virtual_flowpaths", pa.int64(), nullable=True),
                pa.field("virtual_nexus", pa.int64(), nullable=True),
                pa.field("hydrolocations", pa.int64(), nullable=True),
                pa.field("lakes", pa.int64(), nullable=True),
                pa.field("nhd", pa.int64(), nullable=True),
                pa.field("lakes_polygons", pa.int64(), nullable=True),
                pa.field("reservoir_da", pa.int64(), nullable=True),
                pa.field("lake_vfp_crosswalk", pa.int64(), nullable=True),
            ]
        )
