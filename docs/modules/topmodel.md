# TOPMODEL Module Documentation

## Overview

The TOPMODEL module is a physically-based, distributed watershed model that simulates hydrologic fluxes of water (infiltration-excess overland flow, saturation overland flow, infiltration, exfiltration, subsurface flow, evapotranspiration, and channel routing) through a watershed.

## Parameter Reference

### Core Parameters

| Name                    | Datatype          | Description                                                                                                    |
|-------------------------|-------------------|----------------------------------------------------------------------------------------------------------------|
| divide_id               | String            | Unique divide identifier                                                                                       |
| num_sub_catchments      | Integer           | Number of sub catchments                                                                                       |
| imap                    | Integer           | Flag for topographic index map input                                                                           |
| twi                     | List [Dictionary] | Topographic wetness index                                                                                      |
| num_topodex_values      | Integer           | Controls how finely the watershed’s topographic index distribution is discretized                              |
| area                    | Integer           | Total subwatershed area                                                                                        |
| num_channels            | Integer           | Number of channels                                                                                             |
| cum_dist_area_with_dist | Float             | Cumulative distribution of catchment area, as a function of distance from the outlet along the channel network |
| dist_from_outlet        | Float             | Distance from outlet                                                                                           |
| szm                     | Float             | Exponential decline parameter of transmissivity                                                                |
| t0                      | Float             | Downslope transmissivity when the soil is saturated to the surface                                             |
| td                      | Float             | Unsaturated zone time delay per unit storage deficit                                                           |
| chv                     | Float             | Average channel flow velocity                                                                                  |
| rv                      | Float             | Internal overland flow routing velocity                                                                        |
| srmax                   | Float             | Maximum root zone storage deficit                                                                              |
| Q0                      | Float             | Initial subsurface flow per unit area                                                                          |
| sr0                     | Float             | Initial root zone storage deficit below field capacity (m)                                                     |
| infex                   | Float             | Whether to call subroutine to do infiltration excess calcs,                                                    |
| xk0                     | Float             | Surface soil hydraulic conductivity                                                                            |
| hf                      | Float             | Wetting front suction for Green & Ampt solution.                                                               |
| dth                     | Float             | Water content change across the wetting front                                                                  |

## Data Structures

### TOPMODEL Configuration Model

The TOPMODEL module uses a Pydantic model to validate and structure configuration parameters:

```python
divide_id: str | int = Field(..., description="The catchment ID")
num_sub_catchments: int = Field(default=1, description="Number of sub catchments")
imap: int = Field(default=1, description="NA")
twi: list[dict] = Field(default=[{"twi": "dist_4.twi"}], description="NA")
num_topodex_values: int = Field(..., description="NA")
area: int = Field(default=1, description="NA")
num_channels: int = Field(default=1, description="Number of channels")
cum_dist_area_with_dist: float = Field(default=1.0, description="NA")
dist_from_outlet: float = Field(..., description="NA")
szm: float = Field(default=0.0125, description="Exponential decline parameter of transmissivity")
t0: float = Field(
    default=0.000075, description="Downslope transmissivity when the soil is saturated to the surface"
)
td: float = Field(default=20, description="Unsaturated zone time delay per unit storage deficit")
chv: float = Field(default=1000, description="Average channel flow velocity")
rv: float = Field(default=1000, description="Internal overland flow routing velocity")
srmax: float = Field(default=0.04, description="Maximum root zone storage deficit")
Q0: float = Field(default=0.0000328, description="Initial subsurface flow per unit area")
sr0: float = Field(default=0, description="Initial root zone storage deficit below field capacity (m)")
infex: float = Field(
    default=0,
    description="Whether to call subroutine to do infiltration excess calcs, Not typically appropriate in catchments where TOPMODEL is applicable (i.e., shallow highly permeable  soils). 0 = FALSE (default)",
)
xk0: float = Field(default=2, description="Surface soil hydraulic conductivity")
hf: float = Field(default=0.1, description="Wetting front suction for Green & Ampt solution.")
dth: float = Field(default=0.1, description="Water content change across the wetting front")
```

## Usage

### Command Line Interface

The TOPMODEL config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "topmodel" \
    --domain "conus_hf" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `topmodel` for TOPMODEL)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The TOPMODEL module is also accessible via REST API:

```http
GET /v1/modules/topmodel/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.

**Response:** Returns a list of TOPMODEL configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_topmodel_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get TOPMODEL parameters
configs = get_topmodel_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000"
)

# Each config is an TOPMODEL pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Divide ID: {config.divide_id}")
    print(f"Num Sub Catchments: {config.num_sub_catchments}")
    print(f"IMAP: {config.imap}")
    print(f"TWI: {config.twi}")
    print(f"Num Topodex Values: {config.num_topodex_values}")
    print(f"...\n")
```
