# LASAM (Lumped Arid/Semi-arid Model) Module Documentation

## Overview

The LASAM (Lumped Arid/Semi-arid Model) module simulates infiltration and runoff based on Layered Green & Ampt with redistribution (LGAR) model. LGAR is a model which partitions precipitation into infiltration and runoff, and is designed for use in arid or semi-arid climates.

## Parameter Reference

### Core Parameters

| Name               | Datatype     | Description                                                                                       |
|--------------------|--------------|---------------------------------------------------------------------------------------------------|
| layer_thickness    | String       | Thickness of each layer                                                                           |
| initial_psi        | String       |                                                                                                   |
| forcing_resolution | String       | Time step (temporal resolution) of the meteorological forcing data                                |
| ponded_depth_max   | String       | Maximum amount of ponded water that is allowed to accumulate on the soil surface                  |
| use_closed_form_G  | Boolean      |                                                                                                   |
| layer_soil_type    | Float        | Type of each soil layer                                                                           |
| max_soil_types     | Integer      |                                                                                                   |
| wilting_point_psi  | String       | Wilting point (the amount of water not available for plants)                                      |
| field_capacity_psi | String       | Capillary head corresponding to volumetric water content at which gravity drainage becomes slower |
| giuh_ordinates     | List [Float] | Time‑discharge values that describe how a watershed responds to a given rainfall event            |
| calib_params       | Boolean      |                                                                                                   |
| adaptive_timestep  | Boolean      |                                                                                                   |
| sft_coupled        | Boolean      |                                                                                                   |
| soil_z             | List [Float] |                                                                                                   |

## Data Structures

### LASAM Configuration Model

The LASAM module uses a Pydantic model to validate and structure configuration parameters:

```python
catchment: str | int = Field(..., description="The catchment ID")
layer_thickness: str = Field(default="200.0[cm]", description="Thickness of each layer (array)")
initial_psi: str = Field(default="2000.0[cm]", description="NA")
forcing_resolution: str = Field(default="3600[sec]", description="NA")
ponded_depth_max: str = Field(
    default="1.1[cm]",
    description="Maximum amount of ponded water that is allowed to accumulate on the soil surface",
)
use_closed_form_G: bool = Field(default=False, description="NA")
layer_soil_type: float = Field(default="", description="Type of each soil layer (array)")
max_soil_types: int = Field(default=15, description="NA")
wilting_point_psi: str = Field(
    default="15495.0[cm]", description="Wilting point (the amount of water not available for plants)"
)
field_capacity_psi: str = Field(
    default="340.9[cm]",
    description="Capillary head corresponding to volumetric water content at which gravity drainage becomes slower",
    serialization_alias="field_capacity",
)
giuh_ordinates: list[float] = Field(default=[0.06, 0.51, 0.28, 0.12, 0.03], description="giuh")
calib_params: bool = Field(default=True, description="NA")
adaptive_timestep: bool = Field(default=True, description="NA")
sft_coupled: bool = Field(..., description="NA")
soil_z: list[float] = Field(default=[10, 30, 100.0, 200.0], description="NA")
```

## Usage

### Command Line Interface

The LASAM config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "lasam" \
    --domain "conus_hf" \
    --catalog "glue" \
    --sft-included "False" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `lasam` for Lumped Arid/Semi-arid Model)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--sft-included`: Denotes that SFT is in the "dep_modules_included" definition
- `--output`: Output directory for configuration files

### REST API

The LASAM module is also accessible via REST API:

```http
GET /v1/modules/lasam/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `sft_included` (optional): If SFT is in the "dep_modules_included" definition (`True`/`False`; default is `False`)

**Response:** Returns a list of LASAM configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_lasam_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get LASAM parameters
configs = get_lasam_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    sft_included="False",
)

# Each config is an LASAM pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Layer Thickness: {config.layer_thickness}")
    print(f"Initial PSI: {config.initial_psi}")
    print(f"Forcing Resolution: {config.forcing_resolution}")
    print(f"Ponded Depth Max: {config.ponded_depth_max}")
    print(f"Use Closed Form G: {config.use_closed_form_G}")
    print(f"...\n")
```
