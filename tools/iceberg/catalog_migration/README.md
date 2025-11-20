# Migrating namespaces from `test` to `prod`

This folder is set up to move AWS test environment iceberg tables to the production (OE) AWS environment. The script `catalog_migration.py` handles this transfer.

> [!NOTE]
> To run this script your AWS test account credentials need to be in your `.env` file, and your AWS prod account credentials need to be in your `prod.env` file as well.

1. Navigate to the root of the project
2. With your credentials inside your `.env` and `.prod.env` files, run the `catalog_migration.py` script:
    ```sh
    uv run python tools/iceberg/catalog_migration/catalog_migration.py
    ```
3. To specify specific namespaces, include them separated by spaces with the `-n`/`--namespaces` flag. No argumet will migrate every table in every namespace:
    ```sh
    # -n and --namespaces are equilavent, use your preference
    # Only migrate conus_hf
    uv run python tools/iceberg/catalog_migration/catalog_migration.py -n conus_hf
    # Migrate ras_xs, hi_hf and conus_reference
    uv run python tools/iceberg/catalog_migration/catalog_migration.py --namespaces ras_xs hi_hf conus_reference
    # Leave out flag to migrate everything in the catalog
    uv run python tools/iceberg/catalog_migration/catalog_migration.py
    ```

The script will handle everything - table creation, schema copying, table overwrites/appends, etc...
Further, the script will ignore cases where the test table is less current than the prod table, so that the test table isn't overwritten by an older snapshot.
