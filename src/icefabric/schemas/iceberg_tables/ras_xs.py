"""Contains the PyIceberg Table schema for Extracted RAS-XS mapped to the hydrofabric"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, DoubleType, NestedField, StringType


class RepresentativeRasXS:
    """The schema for RAS XS extracted to the hydrofabric

    Attributes
    ----------
    - flowpath_id: The flowpath id from the reference hydrofabric that the current RAS XS aligns is conflated to
    - TW: Channel Top width (ft)
    - Y: Channel depth (ft)
    - river_station: River station from median cross-section within the flowpath
    - model: The submodel from which the XS was extracted from
    - r: Dingmans R coefficient (-)
    - source_river_station: Original river station from source dataset
    - metdata_units: Metadata units
    - epsg: EPSG coordinate system code
    - crs_units: Coordinate reference system units
    - ftype: Feature type classification
    - streamorde: Stream order of the mapped reference flowpath
    - geometry: Binary Linestring geometry data (WKB format)
    - min_x: The minimum longitude associated with the linestring geometry data
    - min_y: The minimum latitude associated with the linestring geometry data
    - max_x: The maximum longitude associated with the linestring geometry data
    - max_y: The maximum latitude associated with the linestring geometry data
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
            "TW",
            "Y",
            "river_station",
            "model",
            "r",
            "source_river_station",
            "metdata_units",
            "epsg",
            "crs_units",
            "ftype",
            "streamorde",
            "geometry",
            "min_x",
            "min_y",
            "max_x",
            "max_y",
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
            NestedField(
                1,
                "flowpath_id",
                StringType(),
                required=True,
                doc="The flowpath id from the reference hydrofabric that the current RAS XS aligns is conflated to",
            ),
            NestedField(2, "TW", DoubleType(), required=False, doc="Channel Top width (ft)"),
            NestedField(3, "Y", DoubleType(), required=False, doc="Channel depth (ft)"),
            NestedField(
                4,
                "river_station",
                DoubleType(),
                required=False,
                doc="River station from median cross-section within the flowpath",
            ),
            NestedField(
                5,
                "model",
                StringType(),
                required=False,
                doc="The submodel from which the XS was extracted from",
            ),
            NestedField(6, "r", DoubleType(), required=False, doc="Dingmans R coefficient (-)"),
            NestedField(
                7,
                "source_river_station",
                DoubleType(),
                required=False,
                doc="Original river station from source dataset",
            ),
            NestedField(8, "metdata_units", StringType(), required=False, doc="Metadata units"),
            NestedField(9, "epsg", DoubleType(), required=False, doc="EPSG coordinate system code"),
            NestedField(
                10, "crs_units", StringType(), required=False, doc="Coordinate reference system units"
            ),
            NestedField(11, "ftype", StringType(), required=False, doc="Feature type classification"),
            NestedField(
                12,
                "streamorde",
                DoubleType(),
                required=False,
                doc="Stream order of the mapped reference flowpath",
            ),
            NestedField(
                13,
                "geometry",
                BinaryType(),
                required=False,
                doc="Binary Linestring geometry data (WKB format)",
            ),
            NestedField(
                14,
                "min_x",
                DoubleType(),
                required=False,
                doc="The minimum longitude associated with the linestring geometry data",
            ),
            NestedField(
                15,
                "min_y",
                DoubleType(),
                required=False,
                doc="The minimum latitude associated with the linestring geometry data",
            ),
            NestedField(
                16,
                "max_x",
                DoubleType(),
                required=False,
                doc="The maximum longitude associated with the linestring geometry data",
            ),
            NestedField(
                17,
                "max_y",
                DoubleType(),
                required=False,
                doc="The maximum latitude associated with the linestring geometry data",
            ),
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
                pa.field("TW", pa.float64(), nullable=True),
                pa.field("Y", pa.float64(), nullable=True),
                pa.field("river_station", pa.float64(), nullable=True),
                pa.field("model", pa.string(), nullable=True),
                pa.field("r", pa.float64(), nullable=True),
                pa.field("source_river_station", pa.float64(), nullable=True),
                pa.field("metdata_units", pa.string(), nullable=True),
                pa.field("epsg", pa.float64(), nullable=True),
                pa.field("crs_units", pa.string(), nullable=True),
                pa.field("ftype", pa.string(), nullable=True),
                pa.field("streamorde", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
                pa.field("min_x", pa.float64(), nullable=True),
                pa.field("min_y", pa.float64(), nullable=True),
                pa.field("max_x", pa.float64(), nullable=True),
                pa.field("max_y", pa.float64(), nullable=True),
            ]
        )


class ConflatedRasXS:
    """The schema for RAS XS extracted to the hydrofabric

    Attributes
    ----------
    - Ym: Mean depth (ft)
    - TW: Channel Top width (ft)
    - flowpath_id: The flowpath id from the reference hydrofabric that the current RAS XS aligns is conflated to
    - river_station: River station from median cross-section within the flowpath
    - model: The submodel from which the XS was extracted from
    - A: Cross-sectional area (sq ft)
    - r: Dingmans R coefficient (-)
    - domain: Domain information
    - river_reach_rs: River reach and river station identifier
    - source_river: Source river name
    - source_reach: Source reach name
    - source_river_station: Original river station from source dataset
    - station_elevation_points: Cross-section elevation points as JSON string
    - bank_stations: Bank station locations as JSON string
    - metdata_units: Metadata units
    - epsg: EPSG coordinate system code
    - crs_units: Coordinate reference system units
    - ftype: Feature type classification
    - streamorde: Stream order of the mapped reference flowpath
    - geometry: Binary Linestring geometry data (WKB format)
    - min_x: The minimum longitude associated with the linestring geometry data
    - min_y: The minimum latitude associated with the linestring geometry data
    - max_x: The maximum longitude associated with the linestring geometry data
    - max_y: The maximum latitude associated with the linestring geometry data
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
            "min_x",
            "min_y",
            "max_x",
            "max_y",
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
            NestedField(1, "Ym", DoubleType(), required=False, doc="Mean depth (ft)"),
            NestedField(2, "TW", DoubleType(), required=False, doc="Channel Top width (ft)"),
            NestedField(
                3,
                "flowpath_id",
                StringType(),
                required=True,
                doc="The flowpath id from the reference hydrofabric that the current RAS XS aligns is conflated to",
            ),
            NestedField(
                4,
                "river_station",
                DoubleType(),
                required=False,
                doc="River station from median cross-section within the flowpath",
            ),
            NestedField(
                5,
                "model",
                StringType(),
                required=False,
                doc="The submodel from which the XS was extracted from",
            ),
            NestedField(6, "A", DoubleType(), required=False, doc="Cross-sectional area (sq ft)"),
            NestedField(7, "r", DoubleType(), required=False, doc="Dingmans R coefficient (-)"),
            NestedField(8, "domain", StringType(), required=False, doc="Domain information"),
            NestedField(
                9,
                "river_reach_rs",
                StringType(),
                required=False,
                doc="River reach and river station identifier",
            ),
            NestedField(10, "source_river", StringType(), required=False, doc="Source river name"),
            NestedField(11, "source_reach", StringType(), required=False, doc="Source reach name"),
            NestedField(
                12,
                "source_river_station",
                DoubleType(),
                required=False,
                doc="Original river station from source dataset",
            ),
            NestedField(
                13,
                "station_elevation_points",
                StringType(),
                required=False,
                doc="Cross-section elevation points as JSON string",
            ),
            NestedField(
                14, "bank_stations", StringType(), required=False, doc="Bank station locations as JSON string"
            ),
            NestedField(15, "metdata_units", StringType(), required=False, doc="Metadata units"),
            NestedField(16, "epsg", DoubleType(), required=False, doc="EPSG coordinate system code"),
            NestedField(
                17, "crs_units", StringType(), required=False, doc="Coordinate reference system units"
            ),
            NestedField(18, "ftype", StringType(), required=False, doc="Feature type classification"),
            NestedField(
                19,
                "streamorde",
                DoubleType(),
                required=False,
                doc="Stream order of the mapped reference flowpath",
            ),
            NestedField(
                20,
                "geometry",
                BinaryType(),
                required=False,
                doc="Binary Linestring geometry data (WKB format)",
            ),
            NestedField(
                21,
                "min_x",
                DoubleType(),
                required=False,
                doc="The minimum longitude associated with the linestring geometry data",
            ),
            NestedField(
                22,
                "min_y",
                DoubleType(),
                required=False,
                doc="The minimum latitude associated with the linestring geometry data",
            ),
            NestedField(
                23,
                "max_x",
                DoubleType(),
                required=False,
                doc="The maximum longitude associated with the linestring geometry data",
            ),
            NestedField(
                24,
                "max_y",
                DoubleType(),
                required=False,
                doc="The maximum latitude associated with the linestring geometry data",
            ),
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
                pa.field("min_x", pa.float64(), nullable=True),
                pa.field("min_y", pa.float64(), nullable=True),
                pa.field("max_x", pa.float64(), nullable=True),
                pa.field("max_y", pa.float64(), nullable=True),
            ]
        )
