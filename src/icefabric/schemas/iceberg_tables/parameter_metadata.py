"""Contains the PyIceberg Table schemas for Hydrofabric v2.2 data model tables"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BooleanType, DoubleType, NestedField, StringType


class ParameterMetadata:
    """Class to represent the parameter metadata table schema"""

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "module",
            "name",
            "calibratable",
            "description",
            "units",
            "data_type",
            "default_value",
            "min",
            "max",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for parameter metadata table
        """
        return Schema(
            NestedField(1, "module", StringType(), required=True),
            NestedField(1, "name", StringType(), required=True),
            NestedField(1, "calibratable", BooleanType()),
            NestedField(1, "description", StringType()),
            NestedField(1, "units", StringType()),
            NestedField(1, "data_type", StringType()),
            NestedField(1, "default_value", StringType()),
            NestedField(1, "min", DoubleType()),
            NestedField(1, "max", DoubleType()),
        )

    @classmethod
    def arrow_schema(cls):
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for divide attributes table
        """
        fields = [
            pa.field("module", pa.string(), nullable=False),
            pa.field("name", pa.string(), nullable=False),
            pa.field("calibratable", pa.bool_()),
            pa.field("description", pa.string()),
            pa.field("units", pa.string()),
            pa.field("data_type", pa.string()),
            pa.field("default_value", pa.string()),
            pa.field("min", pa.float64()),
            pa.field("max", pa.float64()),
        ]

        return pa.schema(fields)
