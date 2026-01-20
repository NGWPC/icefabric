import argparse

from pyiceberg.catalog import load_catalog


def update_schema(namespace: str, table: str, old_column_name: str, new_column_name: str) -> None:
    """Updates the iceberg table schema for a column name

    Parameters
    ----------
    namespace : str
       The namespace where the table to be updated is located
    table : str
       The name of the table to be updated
    old_column_name : str
       The old column name
    new_column_name : str
       The new column name
    """
    table_name = f"{namespace}.{table}"
    catalog = load_catalog("glue")
    table = catalog.load_table(table_name)

    print("original schema: \n")
    print(table.schema)

    with table.update_schema() as schema_update:
        schema_update.rename_column(old_column_name, new_column_name)

    print("new schema: \n")
    print(table.schema)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to update an iceberg table column name")

    parser.add_argument("--namespace", help="The namespace where the table to be updated is located")
    parser.add_argument("--table", help="The name of the table to be updated")
    parser.add_argument("--old_column_name", help="The old column name")
    parser.add_argument("--new_column_name", help="The new column name")

    args = parser.parse_args()
    update_schema(
        namespace=args.namespace,
        table=args.table,
        old_column_name=args.old_column_name,
        new_column_name=args.new_column_name,
    )
