# SMP (Soil Moisture Profile) Module Documentation

## Overview

The SMP (Soil Moisture Profile) module provides soil moisture information distributed over a one-dimensional vertical column and depth to water table. It facilitates coupling among hydrological and thermal models such as (CFE and SFT or LASAM and SFT).

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### SMP Configuration Model

The SMP module uses a Pydantic model to validate and structure configuration parameters:

```python
class SMP(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    verbosity: str = Field(default="none", description="Verbosity level")
    soil_params_smcmax: float = Field(..., description="Maximum soil moisture content", alias="smcmax")
    soil_params_b: float = Field(..., description="Soil moisture retention curve parameter (bexp)", alias="b")
    soil_params_satpsi: float = Field(..., description="Saturated soil suction (psisat)", alias="satpsi")
    soil_z: list[float] = Field(default=[0.1, 0.3, 1.0, 2.0], description="Soil depth layers in meters")
    soil_moisture_fraction_depth: float = Field(
        default=0.4, description="Soil moisture fraction depth in meters"
    )
    soil_storage_model: str = Field(
        default="NA",
        description="If conceptual, conceptual models are used for computing the soil moisture profile (e.g., CFE). If layered, layered-based soil moisture models are used (e.g., LGAR). If topmodel, topmodel's variables are used",
    )
    soil_storage_depth: str = Field(
        default="none",
        description="Depth of the soil reservoir model (e.g., CFE). Note: this depth can be different from the depth of the soil moisture profile which is based on soil_z",
    )
    water_table_based_method: str = Field(
        default="NA",
        description="Needed if soil_storage_model = topmodel. flux-based uses an iterative scheme, and deficit-based uses catchment deficit to compute soil moisture profile",
    )
    soil_moisture_profile_option: str = Field(
        default="NA",
        description="Constant for layered-constant profile. linear for linearly interpolated values between two consecutive layers. Needed if soil_storage_model = layered",
    )
    soil_depth_layers: str = Field(
        default="NA", description="Absolute depth of soil layers. Needed if soil_storage_model = layered"
    )
    water_table_depth: str = Field(default="NA", description="N/A")
```

## Usage

### Command Line Interface

The SMP config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "smp" \
    --domain "conus" \
    --catalog "glue" \
    --smp-extra-module "cfe_x" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "smp" for Soil Moisture Profile)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--smp-extra-module`: Name of another module to be used alongside SMP to fill out additional parameters (must be "cfe_s", "cfe_x", "lasam", or "topmodel")
- `--output`: Output directory for configuration files

### REST API

The SMP module is also accessible via REST API:

```http
GET /modules/smp/?identifier=01010000&domain=conus&module=CFE-X
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `module` (optional): Denotes if another module should be used to obtain additional SMP parameters. (default: None)

**Response:** Returns a list of SMP configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_smp_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SMP parameters
configs = get_smp_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    module="cfe_x"
)

# Each config is an SMP pydantic model
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
{catchment_id}_bmi_config_smp.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
