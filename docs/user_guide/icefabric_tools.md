# Icefabric Tools

A series of compute services built on top of version controlled EDFS data

## Localize Glue Catalog

### Overview

Script located at `tools/local_catalog_sync.py` - downloads the Icefabric catalog from S3 and rewrites paths for local use.

!!! warning "Important"
    To run this tool, your AWS test account credentials need to be in your `.env` file. The `.env` file is used for interacting with the test environment (`.prod.env` for the production environment.)

### Usage

Simply run the python script as-is - no options or flags to set. The script will pull down the Glue catalog from S3 and save the catalog locally. This local catalog can then be archived/imaged for later use. The path to the new warehouse will be `/tmp/icefabric_local_catalog/warehouse`:

```sh
uv run python tools/local_catalog_sync.py
```

## Localize Icechunk (Streamflow) Store

### Overview

Script located at `tools/localize_streamflow.py` - downloads the Icechunk store from S3 to the local filesystem.

!!! warning "Important"
    To run this tool, your AWS test account credentials need to be in your `.env` file. The `.env` file is used for interacting with the test environment (`.prod.env` for the production environment.)

### Usage

As with localizing the Glue catalog, run the python script as-is. The script will save the Icechunk store locally. The path to the new local icechunk store will be `/tmp/icefabric_streamflow_obs`:

```sh
uv run python tools/localize_streamflow.py
```

## Hydrofabric Geospatial Tools

### Overview

The Hydrofabric Geospatial Tools module provides Python functions for subsetting and analyzing hydrofabric data stored in Apache Iceberg format

### Functionality

- **Data Subsetting** - the `subset()` function provides all upstream catchments related to a given gauge

### Usage Examples

#### Basic Subsetting

```python
from pathlib import Path
from pyiceberg.catalog import load_catalog
from icefabric_tools import subset, IdType

# Load the catalog using default settings
catalog = load_catalog("glue")

# Basic subset using a hydrofabric ID
result = subset_hydrofabric(
    catalog=catalog,
    identifier="wb-10026",
    id_type=IdType.ID,
    layers=["divides", "flowpaths", "network", "nexus"]
)

# Access the filtered data
flowpaths = result["flowpaths"]
divides = result["divides"]
network = result["network"]
nexus = result["nexus"]
```

#### Export to GeoPackage

```python
# Export subset directly to GeoPackage
output_path = Path("subset_output.gpkg")

subset_hydrofabric(
    catalog=catalog,
    identifier="01031500",
    id_type=IdType.POI_ID,
    layers=["divides", "flowpaths", "network", "nexus", "pois"],
    output_file=output_path
)
```

#### Getting all layers

```python
# Include all available layers
all_layers = [
    "divides", "flowpaths", "network", "nexus",
    "divide-attributes", "flowpath-attributes",
    "flowpath-attributes-ml", "pois", "hydrolocations"
]

result = subset_hydrofabric(
    catalog=catalog,
    identifier="HUC12-010100100101",
    id_type=IdType.HL_URI,
    layers=all_layers
)

# Process specific layers
pois_data = result["pois"]
attributes = result["flowpath-attributes"]
```
