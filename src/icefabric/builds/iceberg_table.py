import os

import pyarrow as pa
import pyarrow.parquet as pq
import s3fs
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    BinaryType,
    BooleanType,
    DoubleType,
    LongType,
    NestedField,
    StringType,
)


class IcebergTable:
    """
    Create a Iceberg table per parquet file w/ its inherited schema set.

    Note: Allows for user to have the option to read parquets from S3 or locally. It is okay to expect
    following warning statements throughout process: "Iceberg does not have a dictionary type. <class
    'pyarrow.lib.DictionaryType'> will be inferred as string on read."

    """

    def __init__(self) -> None:
        # Generate folder for iceberg catalog
        if not os.path.exists(f"{os.getcwd()}/iceberg_catalog"):
            os.makedirs(f"{os.getcwd()}/iceberg_catalog")

        # Initialize namespace to be set for Iceberg catalog
        self.namespace = ""

    def read_data_dirs(self, data_dir: str) -> list:
        """
        Extract the list of parquet directories.

        Args:
            data_dir (str): Parent directory of the parquet files.
                            Note: All the ml_auxiliary_data parquet
                            files are save under same filenames,
                            but categorized by 'vpuid' conditions.

        Return (list): List of directories associated with each parquet file.

        """
        parquet_list = []
        for folder, _subfolders, files in os.walk(data_dir):
            if folder != data_dir:
                for file in files:
                    parquet_list.append(f"{folder}/{file}")

        return parquet_list

    def read_data(self, parquet_file_path: str) -> pa.Table:
        """
        Load a single parquet as a Pyarrow table.

        Args:
            parquet_file_path (str): Directory of a single parquet.


        Return: A Pyarrow table.

        """
        data = pq.read_table(parquet_file_path)

        return data

    def establish_catalog(
        self, catalog_name: str, namespace: str, catalog_settings: dict[str, str] | None = None
    ) -> None:
        """
        Creates a new Iceberg catalog.

        Defaults to saving in ./iceberg_catalog/{catalog_name}_catalog.db if no uri
        specified in catalog_settings
        Specify 'uri' and 'warehouse' to select location for catalog and files

        Args:
            catalog_name (str): Name of the catalog to be created.
                                Default: 'dev' for development catalog
            namespace (str): Name of namespace.
            catalog_settings (str): Optional catalog settings accepted by pyiceberg.load_catalog()

        Return: None

        """
        # Check if catalog settings exist, if not initialize a URI and warehouse to default location
        if not catalog_settings or not isinstance(catalog_settings, dict):
            catalog_settings = {}
        catalog_settings["uri"] = (
            f"sqlite:///iceberg_catalog/{catalog_name}_catalog.db"
            if "uri" not in catalog_settings.keys()
            else catalog_settings["uri"]
        )
        catalog_settings["warehouse"] = (
            "file://iceberg_catalog"
            if "warehouse" not in catalog_settings.keys()
            else catalog_settings["warehouse"]
        )

        # Establish a new Iceberg catalog & its configuration
        self.catalog = load_catalog(
            name=catalog_name,
            **catalog_settings,
        )

        # Establish namespace to be create w/in catalog
        self.namespace = namespace
        if self.namespace not in self.catalog.list_namespaces():
            self.catalog.create_namespace(self.namespace)

        return

    def convert_pyarrow_to_iceberg_schema(self, arrow_schema: Schema) -> Schema:
        """
        Translate a given Pyarrow schema into a schema acceptable by Iceberg.

        Args:
            arrow_schema (object): Pyarrow schema read from the loaded
                                   parquet of interest.

        Return (Iceberge.Schema): Iceberg schema

        """
        fields = []
        for idx in range(len(arrow_schema)):
            # Extraction of the datatype & name of each schema row
            field_name = arrow_schema.field(idx).name
            arrow_type = arrow_schema.field(idx).type

            # Iceberg datatypes to pyarrow datatypes
            if pa.types.is_int32(arrow_type):
                iceberg_type = LongType()
            elif pa.types.is_string(arrow_type):
                iceberg_type = StringType()
            elif pa.types.is_float64(arrow_type):
                iceberg_type = DoubleType()
            elif pa.types.is_int64(arrow_type):
                iceberg_type = LongType()
            elif pa.types.is_boolean(arrow_type):
                iceberg_type = BooleanType()
            elif pa.types.is_binary(arrow_type):
                iceberg_type = BinaryType()
            elif pa.types.is_dictionary(arrow_type):
                if pa.types.is_string(arrow_type.value_type):
                    iceberg_type = StringType()
                elif pa.types.is_int32(arrow_type.value_type):
                    iceberg_type = LongType()
            else:
                raise ValueError(f"Unsupported PyArrow type: {arrow_type}")

            # Establish the new schema acceptable to Iceberg
            fields.append(
                NestedField(field_id=idx + 1, required=False, name=field_name, field_type=iceberg_type)
            )
        # Iceberg schema
        schema = Schema(*fields)

        return schema

    def create_table_for_parquet(self, iceberg_tablename: str, data_table: pa.Table, schema: Schema) -> None:
        """
        Convert parquet Pyarrow table to iceberg table & allocate Iceberg catalog under the ./iceberg_catalog directory.

        Args:
            iceberg_tablename (str): Name of the Iceberg table to be created.

            data_table (object): Pyarrow table

            schema (object): Unique Iceberg schema to be set for the Iceberg table.

            namespace (str): Namespace for which the Iceberg table will reside within
                             the Iceberg catalog.

        Return: None

        """
        # Create an Iceberg table
        iceberg_table = self.catalog.create_table(
            identifier=f"{self.namespace}.{iceberg_tablename}", schema=schema
        )

        # Updates the Iceberg table with data of interest.
        iceberg_table.append(data_table)

        return

    def create_table_for_all_parquets(self, parquet_files: list[str], app_name: str = "mip-xs") -> None:
        """
        Convert parquets to Iceberg tables - each w/ their inherited schema.

        Args:
            parquet_files (list): List of directories of the parquet files.

            app_name (str): Application to create Iceberg tables.
                            Options: 'mip-xs' & 'bathymetry_ml_auxiliary'

        Return: None

        Note: The sourced data structures for the data in 'mip-xs' &
        'bathymetry_ml_auxiliary' S3 buckets differ.

        """
        for _idx, parquet_file in enumerate(parquet_files):
            if app_name == "mip_xs":
                iceberg_tablename = f"{os.path.split(os.path.split(parquet_file)[1])[1].split('.')[0]}"

            elif app_name == "bathymetry_ml_auxiliary":
                iceberg_tablename = f"{os.path.split(os.path.split(parquet_file)[0])[1]}"

            data_table = self.read_data(parquet_file)
            data_pyarrow_schema = data_table.schema
            schema = self.convert_pyarrow_to_iceberg_schema(data_pyarrow_schema)
            self.create_table_for_parquet(iceberg_tablename, data_table, schema)
        return

    def create_table_for_all_s3parquets(self, app_name: str, bucket_name: str) -> None:
        """
        Convert parquets from S3 to Iceberg tables - each w/ their inherited schema.

        Parameters
        ----------
        app_name : str
            Application to create Iceberg tables.
            Options: 'mip_xs', 'ble_xs' & 'bathymetry_ml_auxiliary'
        bucket_name : str
            S3 bucket name.

        Returns
        -------
        None

        """
        fs = s3fs.S3FileSystem(
            key=os.environ["AWS_ACCESS_KEY_ID"],
            secret=os.environ["AWS_SECRET_ACCESS_KEY"],
            token=os.environ["AWS_SESSION_TOKEN"],
        )
        glob_patterns = {
            "mip_xs": f"{bucket_name}/full_mip_xs_data/**/*.parquet",
            "ble_xs": f"{bucket_name}/full_ble_xs_data/**/*.parquet",
            "bathymetry_ml_auxiliary": f"{bucket_name}/ml_auxiliary_data/**/*.parquet",
        }
        if app_name not in glob_patterns:
            raise KeyError(f"App {app_name} not supported. Please add your app to the glob_patterns")

        # Table Name Factory
        parquet_files = fs.glob(glob_patterns[app_name])
        pyarrow_tables = {}
        for file_path in parquet_files:
            if app_name in {"mip_xs", "ble_xs"}:
                # Extracts the HUC as the table name
                table_name = file_path.split("/")[-1].removesuffix(".parquet")
            elif app_name in {"bathymetry_ml_auxiliary"}:
                # Extract vpuid from directory structure
                table_name = file_path.split("/")[-2]
            else:
                raise KeyError(f"App {app_name} not supported. Please add your app the table name factory")
            s3_uri = f"s3://{file_path}"
            pyarrow_tables[table_name] = pq.read_table(s3_uri, filesystem=fs)

        for table_name, data_table in pyarrow_tables.items():
            schema = self.convert_pyarrow_to_iceberg_schema(data_table.schema)
            self.create_table_for_parquet(table_name, data_table, schema)
