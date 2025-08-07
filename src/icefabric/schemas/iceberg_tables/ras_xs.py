"""Contains the PyIceberg Table schema for Extracted RAS-XS mapped to the hydrofabric"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, DoubleType, NestedField, StringType


class ExtractedRasXS:
    """The schema for RAS XS extracted to the hydrofabric

    Attributes
    ----------
    - flowpath_id: The flowpath id the RAS XS aligns to in the reference hydrofabric
    - r: Dingmans R coefficient (-)
    - TW: Channel Top width (ft)
    - Y: Channel depth (ft)
    - source_river_station: Original river station from source dataset
    - river_station: River station fraom median cross-section within the flowpath
    - model: The submodel from which the XS was extracted from. ex: '/ble_05119_Pulaski/submodels/15312271/15312271.gpkg'
    - ftype: Feature type classification. ex: ['StreamRiver', 'CanalDitch', 'ArtificialPath', 'Connector', None, 'Pipeline']
    - streamorde: Stream order of the mapped reference flowpath
    - geometry: Binary Linestring geometry data (WKB format)
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
            "flowpath_id",
            "r",
            "TW",
            "Y",
            "source_river_station",
            "river_station",
            "model",
            "ftype",
            "streamorde",
            "geometry",
            "metdata_units",
            "epsg",
            "crs_units",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for RAS XS table
        """
        return Schema(
            NestedField(1, "flowpath_id", StringType(), required=True),
            NestedField(2, "r", DoubleType(), required=False),
            NestedField(3, "TW", DoubleType(), required=False),
            NestedField(4, "Y", DoubleType(), required=False),
            NestedField(5, "source_river_station", DoubleType(), required=False),
            NestedField(6, "river_station", DoubleType(), required=False),
            NestedField(7, "model", StringType(), required=False),
            NestedField(8, "ftype", StringType(), required=False),
            NestedField(9, "streamorde", DoubleType(), required=False),
            NestedField(10, "geometry", BinaryType(), required=False),
            NestedField(11, "metdata_units", StringType(), required=False),
            NestedField(12, "epsg", DoubleType(), required=False),
            NestedField(13, "crs_units", StringType(), required=False),
            identifier_field_ids=[1],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for RAS XS table
        """
        return pa.schema(
            [
                pa.field("flowpath_id", pa.string(), nullable=False),
                pa.field("r", pa.float64(), nullable=True),
                pa.field("TW", pa.float64(), nullable=True),
                pa.field("Y", pa.float64(), nullable=True),
                pa.field("source_river_station", pa.float64(), nullable=True),
                pa.field("river_station", pa.float64(), nullable=True),
                pa.field("model", pa.string(), nullable=True),
                pa.field("ftype", pa.string(), nullable=True),
                pa.field("streamorde", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
                pa.field("metdata_units", pa.string(), nullable=True),
                pa.field("epsg", pa.float64(), nullable=True),
                pa.field("crs_units", pa.string(), nullable=True),
            ]
        )
