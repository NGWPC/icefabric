import argparse

from pyiceberg.catalog import Catalog, load_catalog

from icefabric.helpers import load_creds


def get_catalog_def(catalog: Catalog, namespaces: list[str] | None = None):
    """
    Given a catalog, extract the definitions of all tables in all namespaces (or specified namespaces).

    Attributes
    ----------
    catalog : Catalog
        The catalog to extract definitions from.
    namespaces : list[str] | None, optional
        List of namespaces to extract definitions from. If None, all namespaces are extracted.

    Returns
    -------
    dict
        A dictionary with namespace names as keys and another dictionary as values.
    """
    catalog_def = {}
    if namespaces is None:
        namespaces = [n[0] for n in catalog.list_namespaces()]
    for ns in namespaces:
        tables = {}
        for t_name in [t[1] for t in catalog.list_tables(ns)]:
            t_def = {}
            t = catalog.load_table(f"{ns}.{t_name}")
            t_def["schema"] = t.schema()
            t_def["partition_spec"] = t.spec()
            t_def["sort_order"] = t.sort_order()
            t_def["properties"] = t.properties
            if t.current_snapshot() is not None:
                t_def["latest_snapshot_time"] = t.current_snapshot().timestamp_ms
            else:
                t_def["latest_snapshot_time"] = None
            tables.update({t_name: t_def})
        catalog_def[ns] = tables
    return catalog_def


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-n",
        "--namespaces",
        nargs="+",
        help="Namespaces you want to migrate. Omitting this will migrate all namespaces.",
        required=False,
    )
    args = parser.parse_args()

    # Authenticate and load both test and prod catalogs
    load_creds("test")
    test_catalog = load_catalog("glue")
    load_creds("prod")
    prod_catalog = load_catalog("glue")

    load_creds("test")
    catalog_def = get_catalog_def(test_catalog, args.namespaces)

    for ns in catalog_def:
        print(f'\nMigrating namespace "{ns}"...')
        ns_props = test_catalog.load_namespace_properties(ns)
        load_creds("prod")
        prod_catalog.create_namespace_if_not_exists(ns, ns_props)
        for t in catalog_def[ns]:
            prod_table_empty, prod_table_update_needed = True, True
            load_creds("test")
            test_table = test_catalog.load_table(f"{ns}.{t}")

            if (ns, t) in prod_catalog.list_tables(ns):
                # Prod table exists already
                load_creds("prod")
                prod_table = prod_catalog.load_table(f"{ns}.{t}")
                if prod_table.current_snapshot() is not None:
                    # Table has existing history
                    prod_table_empty = False
                    pt_ts = prod_table.current_snapshot().timestamp_ms
                    if catalog_def[ns][t]["latest_snapshot_time"] < pt_ts:
                        # Prod table is up-to-date
                        print(f'Prod table "{ns}.{t}" is more recent than test table - skipping...')
                        prod_table_update_needed = False
            else:
                # Prod table does not exist
                print(f'First, creating table "{ns}.{t}" in production catalog...')
                new_location = f"s3://iceberg-data-oe/icefabric_catalog/{ns}/{t}"
                load_creds("prod")
                prod_table = prod_catalog.create_table(
                    identifier=f"{ns}.{t}",
                    schema=catalog_def[ns][t]["schema"],
                    location=new_location,
                    partition_spec=catalog_def[ns][t]["partition_spec"],
                    sort_order=catalog_def[ns][t]["sort_order"],
                    properties=catalog_def[ns][t]["properties"],
                )

            load_creds("test")
            if catalog_def[ns][t]["latest_snapshot_time"] is None or test_table.scan().count() == 0:
                # Test table is empty
                print(f'Test table "{ns}.{t}" has no data - no migration will take place - skipping...')
                prod_table_update_needed = False

            if prod_table_update_needed:
                print(f'Migrating table "{ns}.{t}"...')
                load_creds("test")
                arrow_table = test_table.scan().to_arrow()
                load_creds("prod")
                if prod_table_empty:
                    prod_table.append(arrow_table)
                else:
                    print(f'Table "{ns}.{t}" exists already in production env. Overwriting...')
                    prod_table.overwrite(arrow_table)
                print(f'Migration successful for namespace "{ns}.{t}"!\n')
        print(f'Migration successful for namespace "{ns}"!\n')
