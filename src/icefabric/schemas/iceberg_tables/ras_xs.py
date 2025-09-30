"""Contains the PyIceberg Table schema for Extracted RAS-XS mapped to the hydrofabric"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, DoubleType, NestedField, StringType


class RepresentativeRasXS:
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


class ConflatedRasXS:
    """The schema for RAS XS extracted to the hydrofabric

    Attributes
    ----------
    - flowpath_id: The flowpath id the RAS XS aligns to in the reference hydrofabric
    - Ym: Mean depth (ft)
    - TW: Channel Top width (ft)
    - A: Cross-sectional area (sq ft)
    - r: Dingmans R coefficient (-)
    - river_station: River station from median cross-section within the flowpath
    - source_river_station: Original river station from source dataset
    - model: The submodel from which the XS was extracted from
    - domain: Domain information
    - river_reach_rs: River reach and river station identifier
    - source_river: Source river name
    - source_reach: Source reach name
    - station_elevation_points: Cross-section elevation points as JSON string
    - bank_stations: Bank station locations as JSON string
    - ftype: Feature type classification
    - streamorde: Stream order of the mapped reference flowpath
    - geometry: Binary Linestring geometry data (WKB format)
    - metdata_units: Metadata units
    - epsg: EPSG coordinate system code
    - crs_units: Coordinate reference system units
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
            "Ym",
            "TW",
            "flowpath_id",
            "river_station",
            "model",
            "A",
            "r",
            "domain",
            "river_reach_rs",
            "source_river",
            "source_reach",
            "source_river_station",
            "station_elevation_points",
            "bank_stations",
            "metdata_units",
            "epsg",
            "crs_units",
            "ftype",
            "streamorde",
            "geometry",
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
            NestedField(1, "Ym", DoubleType(), required=False),
            NestedField(2, "TW", DoubleType(), required=False),
            NestedField(3, "flowpath_id", StringType(), required=True),
            NestedField(4, "river_station", DoubleType(), required=False),
            NestedField(5, "model", StringType(), required=False),
            NestedField(6, "A", DoubleType(), required=False),
            NestedField(7, "r", DoubleType(), required=False),
            NestedField(8, "domain", StringType(), required=False),
            NestedField(9, "river_reach_rs", StringType(), required=False),
            NestedField(10, "source_river", StringType(), required=False),
            NestedField(11, "source_reach", StringType(), required=False),
            NestedField(12, "source_river_station", DoubleType(), required=False),
            NestedField(13, "station_elevation_points", StringType(), required=False),
            NestedField(14, "bank_stations", StringType(), required=False),
            NestedField(15, "metdata_units", StringType(), required=False),
            NestedField(16, "epsg", DoubleType(), required=False),
            NestedField(17, "crs_units", StringType(), required=False),
            NestedField(18, "ftype", StringType(), required=False),
            NestedField(19, "streamorde", DoubleType(), required=False),
            NestedField(20, "geometry", BinaryType(), required=False),
            identifier_field_ids=[3],
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
                pa.field("Ym", pa.float64(), nullable=True),
                pa.field("TW", pa.float64(), nullable=True),
                pa.field("flowpath_id", pa.string(), nullable=False),
                pa.field("river_station", pa.float64(), nullable=True),
                pa.field("model", pa.string(), nullable=True),
                pa.field("A", pa.float64(), nullable=True),
                pa.field("r", pa.float64(), nullable=True),
                pa.field("domain", pa.string(), nullable=True),
                pa.field("river_reach_rs", pa.string(), nullable=True),
                pa.field("source_river", pa.string(), nullable=True),
                pa.field("source_reach", pa.string(), nullable=True),
                pa.field("source_river_station", pa.float64(), nullable=True),
                pa.field("station_elevation_points", pa.string(), nullable=True),
                pa.field("bank_stations", pa.string(), nullable=True),
                pa.field("metdata_units", pa.string(), nullable=True),
                pa.field("epsg", pa.float64(), nullable=True),
                pa.field("crs_units", pa.string(), nullable=True),
                pa.field("ftype", pa.string(), nullable=True),
                pa.field("streamorde", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )
