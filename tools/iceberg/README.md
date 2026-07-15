### Pushing to prod

This folder is set up to create/update production iceberg S3 Tables on the AWS test account.

To ensure that we don't accidentally override data before our code for data manipulation is accurate, the following strategy is being proposed. There will be three steps to data promotion from Dev → Test → Prod

Dev
Pyiceberg namespaces and tables can both exist in a centralized location and a local directory on a user's system. Through using the `export_catalog.py` script, a namespace can be locally created in the /tmp  directory using SQLlite/DuckDB. Since these local tables are detached from the production data lake, the code/data is safe for all development/manipulation

Test
Once code is vetted and merged into Github, tests of code services be done locally through read-only queries of the production glue catalog. These can be done through changing the catalog name from sql  to glue .

Prod
After code passes test, we can begin to update the Production glue catalog with any data that was manipulated by the code. The S3 table will be updated, with the new snapshot noted with the specific delivery. Any snapshots which require additional backups will be downloaded into the edfs-data/ into a folder specified by the snapshot ID.

<img src="../../docs/img/production_promotion.png" alt="Production promotion" width="70%">

When writing update scripts, it's important to know the location of the data that you're writing to. Uploading data to S3 Tables tracks the file location, which all should live on the Test account.

<img src="../../docs/img/test_account_overview.png" alt="Production promotion" width="70%">

### Snapshot-preserving NHF update

`build_nhf.py` updates existing tables with Iceberg overwrites; it does not purge tables. Before any
catalog mutation it writes a JSON manifest containing every table's metadata location, schema, refs,
and snapshot history. It also tags every current data snapshot as `pre_<release-tag>` before writing.
The strict converter guarantees that every layer present in a GeoPackage is converted. Use
`--require-all` only for domains expected to contain every supported layer; domain-specific packages
may legitimately omit layers such as Alaska's `lakes_polygons`.

```sh
# Convert and validate every NHF GeoPackage layer.
uv run python tools/hydrofabric/nhf_gpkg_to_parquet.py \
  --gpkg /path/to/nhf_1.2.2.gpkg \
  --output-folder /tmp/nhf_1_2_2 \
  --strict

# Inspect each Test namespace without changing Glue or S3.
uv run python tools/iceberg/build_nhf.py \
  --catalog glue --deploy-env test --namespace conus_nhf \
  --files /tmp/nhf_1_2_2 --overwrite --require-all --dry-run \
  --release-tag nhf_1_2_2 \
  --backup-manifest output/conus_nhf_pre_nhf_1_2_2.json

uv run python tools/iceberg/build_nhf.py \
  --catalog glue --deploy-env test --namespace nhf \
  --files /tmp/nhf_1_2_2 --overwrite --require-all --dry-run \
  --release-tag nhf_1_2_2 \
  --backup-manifest output/nhf_pre_nhf_1_2_2.json
```

After reviewing the dry-run, remove `--dry-run` to apply the update. Run the two namespaces separately
so `conus_nhf` can be tested as a canary before updating the legacy `nhf` namespace. Existing tables
that are not in the GeoPackage remain registered.

For data rollback, use the recorded snapshot IDs with `tools/iceberg/set_snapshot.py`. A snapshot
rollback does not restore an incompatible schema change; for that case, use the manifest's recorded
`metadata_location` to restore the prior table registration.

### Example workflow

For this workflow I'll be showing how to update the CONUS hydrofabric namespace

#### Build/Create

*Note* this assumes you have a .gpkg file that you'd like to upload to PyIceberg

1. Write the geopackage to a parquet

```sh
python tools/hydrofabric/gpkg_to_parquet.py --gpkg conus_hf.gpkg --output-folder /tmp/hf
```

1. Build a local warehouse for testing using the sql warehouse

```sh
python tools/iceberg/build_hydrofabric.py --catalog sql --files /tmp/hf --domain conus
```

1. Test that this is working, confirm with a team member in peer review

2. Update the GLUE endpoint

```sh
python tools/iceberg/build_hydrofabric.py --catalog glue --files /tmp/hf --domain conus
```

#### Update

1. Export the table you are looking to update from the S3 Tables so you have a local dev warehouse

```sh
python tools/iceberg/export_catalog.py --namespace conus_hf
```

1. Download the gpkg so you can make changes

```sh
python tools/hydrofabric/download_hydrofabric_gpkg.py --namespace conus_hf
```

1. Make changes to the geopackage

2. Write the geopackage to a parquet

```sh
python tools/hydrofabric/gpkg_to_parquet.py --gpkg patch_conus_hf.gpkg --output-folder /tmp/hf
```

1. Update the local warehouse table

```sh
python tools/iceberg/update_hydrofabric.py --layer <LAYER> --file </tmp/hf/FILE TO BE UPDATED> --domain conus
```

1. Once the data is updated and works, confirm with a team member that the data is correct, then prod can be updated

```sh
python tools/iceberg/update_hydrofabric.py --catalog glue --layer <LAYER> --file </tmp/hf/FILE TO BE UPDATED> --domain conus
```
