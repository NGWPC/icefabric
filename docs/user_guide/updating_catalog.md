# Updating the Iceberg Catalog from an NHF GeoPackage

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

   Note: Make sure to use the NHF-specific converter rather than the generic `gpkg_to_parquet.py`.

3. **Apply the Test update**

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

   Note: `--require-all` is appropriate for domains expected to contain every
   supported layer, such as CONUS. Omit it for domains that legitimately lack
   some layers. Like Alaska which doesn't have the polygon layer

  The script will:
   - Create a backup manifest.The manifest's recorded snapshot can be used to rollback or for more manual schema/catalog recovery if necessary.
   - Tag existing snapshots as `pre_nhf_1_2_2`.
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

# Rollback

If rollback is needed, use the snapshot IDs recorded in the backup manifest
with `tools/iceberg/set_snapshot.py`.
