# Updating the Iceberg Catalog from an NHF GeoPackage

This is a guide for updating NHF but can be adapted to other namespaces. For another namespace, follow the general rules and create a specific build script in the `tools/iceberg` folder. You will need a schema, parquets, and a build script.

**Schema Change**

If you are changing the schema (changing columns in a layer or adding a layer), go to `src/icefabric/schemas/hydrofabric_update.py` (this is NHF).
For each layer, there is a class with the layer name.

- Add the new columns to the field list in docstring
- Add the columns to the `def columns` classmethod.
- Add bew columns to the `def schema` classmethod. This is for pyiceberg. Add the description at the correct index in the list and add a `NestedField`. Note that the first argument is 1-indexed and the description arugment is 0-indexed (python list). Include the data type.
- Add the columns to the `def arrow_schema` classmethod. These are `pa.field`. Use `pa` datatypes.

If you are adding a layer, create a new class with the same pattern as the other layers. You also need to add it to `nhf_layers` in `src/icefabric/iceberg_table/__init__.py/nhf_layers`. These are the supported layers for when you convert from GPKG to parquet.

When you run `build_nhf` in step 4 and the layer is present in the parquets, it will pick it up and add it to icefabric.

1. **Configure credentials**

   Put Test AWS credentials in `.env` at the project root, or Production AWS
   credentials in `.prod.env`.

2. **Convert the NHF GeoPackage to layer-specific Parquet files**

   ```bash
   uv run python tools/hydrofabric/nhf_gpkg_to_parquet.py \
     --gpkg /path/to/nhf_1.2.2.gpkg \
     --output-folder /tmp/nhf_1_2_2 \
     --strict
   ```

   Note: Make sure to use the NHF-specific converter rather than the HFv2.2 converter (`hf2.2_gpkg_to_parquet.py`).

3. **Apply the Test update**
   If using SQL, change `glue` to `sql`

   ```bash
   uv run python tools/iceberg/build_nhf.py \
     --catalog glue \
     --deploy-env test \
     --namespace conus_nhf \
     --files /tmp/nhf_1_2_2 \
     --overwrite \
     --require-all \
     --release-tag nhf_1_2_2 \
     --backup-manifest output/conus_nhf_pre_nhf_1_2_2.json
   ```
   Replace 1_2_2 with major_minor_patch version.

   Note: `--require-all` is appropriate for domains expected to contain every
   supported layer, such as CONUS. Omit it for domains that legitimately lack
   some layers. Like Alaska which doesn't have the polygon layer

  The script will:
   - Create a backup manifest.The manifest's recorded snapshot can be used to rollback or for more manual schema/catalog recovery if necessary.
   - Tag existing snapshots as `pre_nhf_major_minor_patch` e.g. `pre_nhf_1_2_2`
   - Synchronize compatible schema changes.
   - Overwrite each supplied table without purging its history.
   - Record the new release snapshots.

4. **Verify the Test catalog and application**

   Query the updated tables or run the API against the Test Glue catalog.
   Compare representative results with the source GeoPackage.

5. **Repeat for additional namespaces for each domain**

   For CONUS, update `conus_nhf` first as a canary. Then repeat the update with:

   ```bash
   --namespace nhf
   ```

   This updates the legacy conus namespace. All the other domains just have one namespace.

## Rollback

If rollback is needed, use the snapshot IDs recorded in the backup manifest
with `tools/iceberg/set_snapshot.py`.
