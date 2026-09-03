# SMP (Soil Moisture Profile) Module Documentation

## Overview

The SMP (Soil Moisture Profile) module provides soil moisture information distributed over a one-dimensional vertical column and depth to water table. It facilitates coupling among hydrological and thermal models such as (CFE and SFT or LASAM and SFT).

## Parameter Reference

### Core Parameters

| Name                         | Datatype     | Description                                                                                                                                             |
|------------------------------|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| soil_params_smcmax           | Float        | Maximum soil moisture content                                                                                                                           |
| soil_params_b                | Float        | Soil moisture retention curve parameter (bexp)                                                                                                          |
| soil_params_satpsi           | Float        | Saturated soil suction (psisat)                                                                                                                         |
| soil_z                       | List [Float] | Soil depth layers in meters                                                                                                                             |
| soil_moisture_fraction_depth | Float        | Soil moisture fraction depth in meters                                                                                                                  |
| soil_storage_model           | String       | Determines type of model used for computing SMP (conceptual, layered or topmodel)                                                                       |
| soil_storage_depth           | Float        | Depth of the soil reservoir model (e.g., CFE). Note: this depth can be different from the depth of the soil moisture profile which is based on soil_z   |
| water_table_based_method     | String       | Needed if soil_storage_model = topmodel. flux-based uses an iterative scheme, and deficit-based uses catchment deficit to compute soil moisture profile |
| soil_moisture_profile_option | String       | Constant for layered-constant profile. linear for linearly interpolated values between two consecutive layers. Needed if soil_storage_model = layered   |
| soil_depth_layers            | Float        | Absolute depth of soil layers. Needed if soil_storage_model = layered                                                                                   |
| water_table_depth            | Float        | The vertical position of the saturated zone in the soil column                                                                                          |

## Data Structures

### SMP Configuration Model

The SMP module uses a Pydantic model to validate and structure configuration parameters:

```python
soil_params_smcmax: FloatWithUnits = Field(
    ...,
    description="Maximum soil moisture content",
    alias="smcmax",
    serialization_alias="smcmax",
)
soil_params_b: FloatWithUnits = Field(
    ...,
    description="Soil moisture retention curve parameter (bexp)",
    alias="b",
    serialization_alias="b",
)
soil_params_satpsi: FloatWithUnits = Field(
    ...,
    description="Saturated soil suction (psisat)",
    alias="satpsi",
    serialization_alias="satpsi",
)
soil_z: FloatListWithUnits = Field(
    default=FloatListWithUnits(value=[0.1, 0.3, 1.0, 2.0], units="m"),
    description="Soil depth layers in meters",
)
soil_moisture_fraction_depth: FloatWithUnits = Field(
    default=FloatWithUnits(value=0.4, units="m"), description="Soil moisture fraction depth in meters"
)
soil_storage_model: str | None = Field(
    ...,
    description="If conceptual, conceptual models are used for computing the soil moisture profile (e.g., CFE). If layered, layered-based soil moisture models are used (e.g., LGAR). If topmodel, topmodel's variables are used",
)
soil_storage_depth: FloatWithUnits | None = Field(
    ...,
    description="Depth of the soil reservoir model (e.g., CFE). Note: this depth can be different from the depth of the soil moisture profile which is based on soil_z",
)
water_table_based_method: str | None = Field(
    ...,
    description="Needed if soil_storage_model = topmodel. flux-based uses an iterative scheme, and deficit-based uses catchment deficit to compute soil moisture profile",
)
soil_moisture_profile_option: str | None = Field(
    ...,
    description="Constant for layered-constant profile. linear for linearly interpolated values between two consecutive layers. Needed if soil_storage_model = layered",
)
soil_depth_layers: FloatWithUnits | None = Field(
    ..., description="Absolute depth of soil layers. Needed if soil_storage_model = layered"
)
water_table_depth: FloatWithUnits | None = Field(default="NA", description="N/A")
```

## Usage

### Command Line Interface

The SMP config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "smp" \
    --domain "conus_hf" \
    --catalog "glue" \
    --smp-extra-module "cfe_x" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `smp` for Soil Moisture Profile)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--smp-extra-module`: Name of another module to be used alongside SMP to fill out additional parameters (must be `cfe_s`, `cfe_x`, `lasam`, or `topmodel`)
- `--output`: Output directory for configuration files

### REST API

The SMP module is also accessible via REST API:

```http
GET /v1/modules/smp/?identifier=01010000&module=CFE-X
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `module` (optional): Denotes if another module (`CFE-S`, `CFE-X`, `LASAM` or `TopModel`) should be used to obtain additional SMP parameters. (default: `None`)

**Response:** Returns a list of SMP configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_smp_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SMP parameters
configs = get_smp_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    extra_module="CFE-X"
)

# Each config is an SMP pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Soil Params SMC Max: {config.soil_params_smcmax}")
    print(f"Soil Params B: {config.soil_params_b}")
    print(f"Soil Params Sat PSI: {config.soil_params_satpsi}")
    print(f"Soil Z: {config.soil_z}")
    print(f"Soil Moisture Fraction Depth: {config.soil_moisture_fraction_depth}")
    print(f"...\n")
```
