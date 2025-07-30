# Icefabric Tools

A series of compute services built on top of version controlled EDFS data

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
