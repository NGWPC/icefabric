import os

from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType

# Define warehouse path as a variable at the top (replace with your actual path or load dynamically)
WAREHOUSE_PATH = os.getenv("ICEBERG_WAREHOUSE_PATH")
TABLE_SUBPATH = "tables/icefabric"  # Please avoid restricted directories

# Debug: Print AWS region and Warehouse environment variables
print(f"AWS_DEFAULT_REGION from env: {os.getenv('AWS_DEFAULT_REGION')}")
print(f"Using warehouse path: {WAREHOUSE_PATH}")

# Configure the catalog to use AWS Glue
config = {
    "type": "glue",
    "s3.endpoint": "s3.us-east-1.amazonaws.com",
    "warehouse": f"{WAREHOUSE_PATH}",
    "region": "us-east-1",
    "glue_region": "us-east-1",
}
print(f"Catalog configuration: {config}")

try:
    catalog = load_catalog("glue", **config)
    print("Catalog loaded successfully")
except Exception as e:
    print(f"Error loading catalog: {e}")
    raise

# Define a schema for the Iceberg table (used if creating the table)
schema = Schema(
    NestedField(field_id=1, name="id", field_type=LongType(), is_optional=False),
    NestedField(field_id=2, name="name", field_type=StringType(), is_optional=True),
)

# Load or create a table in the Glue catalog, pointing to S3 for storage
try:
    table = catalog.load_table(("icefabric_db", "icefabric"))
    print(f"Table loaded: {str(table)}")
except Exception as e:
    print(f"Table not found, creating it: {e}")
    try:
        table = catalog.create_table(
            identifier=("icefabric_db", "icefabric"), schema=schema, location=f"{TABLE_SUBPATH}"
        )
        print(f"Table created: {str(table)}")
    except Exception as create_error:
        print(f"Error creating table: {create_error}")
        raise

# Example: List tables in the catalog to verify
try:
    tables = catalog.list_tables("icefabric_db")
    print(f"Tables in namespace: {tables}")
except Exception as list_error:
    print(f"Error listing tables: {list_error}")
