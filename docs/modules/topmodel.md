# TOPMODEL Module Documentation

## Overview

The TOPMODEL module is a physically-based, distributed watershed model that simulates hydrologic fluxes of water (infiltration-excess overland flow, saturation overland flow, infiltration, exfiltration, subsurface flow, evapotranspiration, and channel routing) through a watershed.

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### TOPMODEL Configuration Model

The TOPMODEL module uses a Pydantic model to validate and structure configuration parameters:

```python
class Topmodel(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    divide_id: str = Field(..., description="The catchment ID")
    num_sub_catchments: int = Field(default=1, description="Number of sub catchments")
    imap: int = Field(default=1, description="NA")
    yes_print_output: int = Field(default=1, description="NA")
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
    --module "topmodel" \
    --domain "conus" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "topmodel" for TOPMODEL)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The TOPMODEL module is also accessible via REST API:

```http
GET /modules/topmodel/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)

**Response:** Returns a list of TOPMODEL configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_topmodel_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get TOPMODEL parameters
configs = get_topmodel_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000"
)

# Each config is an TOPMODEL pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    # TODO - show more
```

## Parameter Estimation

The system automatically estimates initial parameters from hydrofabric data:

TODO

## Output Files

The CLI and API generate BMI-compatible configuration files:

```
{catchment_id}_bmi_config_topmodel.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
