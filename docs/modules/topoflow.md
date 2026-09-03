# Topoflow Module Documentation

## Overview

A glacier energy balance module as part of TopoFlow, an open source, BMI compatible, modularized, distributed hydrologic model in Python.

## Parameter Reference

### Core Parameters

| Name            | Datatype | Description                                                                 |
|-----------------|----------|-----------------------------------------------------------------------------|
| da              | Float    | Drainage area                                                               |
| slope           | Float    | Terrain slope in degrees                                                    |
| aspect          | Float    | Terrain aspect in degrees                                                   |
| lat             | Float    | Y coordinates of divide centroid                                            |
| lon             | Float    | X coordinates of divide centroid                                            |
| elev            | Float    | Elevation from DEM                                                          |
| h_active_layer  | Float    | Percentage of catchment that is glaciated                                   |
| h0_snow         | Float    | Initial snow depth at simulation start                                      |
| h0_ice          | Float    | Initial ice thickness at simulation start                                   |
| h0_swe          | Float    | Initial amount of snow water equivalent (SWE) at simulation start           |
| h0_iwe          | Float    | Initial amount of ice water equivalent (IWE) at simulation start            |
| T_rain_snow     | Float    | Air‑temperature threshold used to partition precipitation into rain or snow |
| glacier_percent | Float    | Proportion of catchment covered by glacier ice                              |

## Data Structures

### Topoflow Configuration Model

The Topoflow module uses a Pydantic model to validate and structure configuration parameters:

```python
da: float = Field(..., description="drainage area")
slope: float = Field(..., description="terrain slope in degrees")
aspect: float = Field(..., description="terrain aspect in degrees")
lat: float = Field(..., description="Y coordinates of divide centroid")
lon: float = Field(..., description="X coordinates of divide centroid")
elev: float = Field(..., description="Elevation from DEM")
h_active_layer: float = Field(
    default=TopoFlowValues.H_ACTIVE_LAYER.value,
    description="",
)
h0_snow: float = Field(
    default=TopoFlowValues.H0_SNOW.value,
    description="",
)
h0_ice: float = Field(
    default=TopoFlowValues.H0_ICE.value,
    description="",
)
h0_swe: float = Field(
    default=TopoFlowValues.H0_SWE.value,
    description="",
)
h0_iwe: float = Field(
    default=TopoFlowValues.H0_IWE.value,
    description="",
)
T_rain_snow: float = Field(
    default=TopoFlowValues.T_RAIN_SNOW.value,
    description="",
)
glacier_percent: float = Field(..., description="Percentage of catchment that is glaciated")
```

## Usage

### Command Line Interface

The Topoflow config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "topoflow" \
    --domain "conus_hf" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `topoflow` for Topoflow)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The Topoflow module is also accessible via REST API:

```http
GET /v1/modules/topoflow/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.

**Response:** Returns a list of Topoflow configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_topoflow_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get Topoflow parameters
configs = get_topoflow_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000"
)

# Each config is a Topoflow pydantic model
for config in configs:
    print(f"Site Prefix: {config.site_prefix}")
    print(f"DA: {config.da}")
    print(f"Slope: {config.slope}")
    print(f"Aspect: {config.aspect}")
    print(f"Lat: {config.lat}")
    print(f"Lon: {config.lon}")
    print(f"...\n")
```
