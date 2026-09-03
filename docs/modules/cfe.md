# CFE Module Documentation

## Overview

CFE (Conceptual Functional Equivalent) is a simplified conceptual model written by Fred Ogden that is designed to be functionally equivalent to the National Water Model.

## Parameter Reference

### Core Parameters

| Name                                    | Datatype     | Description                                                                                                                            |
|-----------------------------------------|--------------|----------------------------------------------------------------------------------------------------------------------------------------|
| surface_water_partitioning_scheme       | String       | Selects Xinanjiang or Schaake                                                                                                          |
| surface_runoff_scheme                   | String       | GIUH (1) or NASH_CASCADE (2)                                                                                                           |
| is_sft_coupled                          | Boolean      | Turns on/off the CFE coupling with the SoilFreezeThaw.                                                                                 |
| ice_content_threshold                   | Float        | Represents the ice content above which soil is impermeable.                                                                            |
| soil_params_b                           | Float        | Beta exponent on Clapp-Hornberger (1978) soil water relations                                                                          |
| soil_params_satdk                       | Float        | Saturated hydraulic conductivity                                                                                                       |
| soil_params_satpsi                      | Float        | Saturated capillary head                                                                                                               |
| soil_params_slop                        | Float        | Modifies the gradient of the hydraulic head at the soil bottom.                                                                        |
| soil_params_smcmax                      | Float        | Saturated soil moisture content (Maximum soil moisture content)                                                                        |
| soil_params_wltsmc                      | Float        | Wilting point soil moisture content (< soil_params.smcmax)                                                                             |
| soil_params_expon                       | Float        | Defines the soil reservoirs to be linear, Use linear reservoirs                                                                        |
| soil_params_expon_secondary             | Float        | Defines the soil reservoirs to be linear, Use linear reservoirs                                                                        |
| max_gw_storage                          | Float        | Maximum storage in the conceptual reservoir                                                                                            |
| Cgw                                     | Float        | Primary outlet coefficient                                                                                                             |
| expon                                   | Float        | Exponent parameter for nonlinear ground water reservoir (1.0 for linear reservoir)                                                     |
| gw_storage                              | Float        | Initial condition for groundwater reservoir - (ground water as a decimal fraction of the maximum groundwater storage (max_gw_storage)) |
| alpha_fc                                | Float        | Alpha at fc for clapp hornberger (field capacity)                                                                                      |
| soil_storage                            | Float        | Initial condition for soil reservoir (water in the soil as a decimal fraction of maximum soil water storage (smcmax x depth))          |
| K_nash                                  | Float        | Nash Config param for lateral subsurface runoff (Nash discharge to storage ratio)                                                      |
| K_lf                                    | Float        | Nash Config param - primary reservoir                                                                                                  |
| nash_storage                            | List [Float] | Nash Config param - secondary reservoir                                                                                                |
| giuh_ordinates                          | List [Float] | Giuh (geomorphological instantaneous unit hydrograph) ordinates in dt time steps                                                       |
| a_Xinanjiang_inflection_point_parameter | Float        | When surface_water_partitioning_scheme=Xinanjiang                                                                                      |
| b_Xinanjiang_shape_parameter            | Float        | When surface_water_partitioning_scheme=Xinanjiang                                                                                      |
| x_Xinanjiang_shape_parameter            | Float        | When surface_water_partitioning_scheme=Xinanjiang                                                                                      |
| urban_decimal_fraction                  | Float        | When surface_water_partitioning_scheme=Xinanjiang                                                                                      |
| refkdt                                  | Float        | Reference Soil Infiltration Parameter (used in runoff formulation)                                                                     |
| soil_params_depth                       | Float        | Soil depth                                                                                                                             |
| is_aet_rootzone                         | Boolean      | Turn on rootzone AET                                                                                                                   |
| soil_layer_depths                       | List [Float] | Array of depths from the surface for AET                                                                                               |
| max_rootzone_layer                      | Float        | Layer of the soil that is the maximum root zone depth                                                                                  |

## Data Structures

### CFE Configuration Model

The CFE module uses a Pydantic model to validate and structure configuration parameters:

```python
catchment: str | int = Field(..., description="The catchment ID")
surface_water_partitioning_scheme: str = Field(..., description="Selects Xinanjiang or Schaake")
surface_runoff_scheme: str = Field(
    default=CFEValues.SRFC_RUNOFF_SCHEME.value,
    description="Accepts  1 or GIUH for GIUH and  2 or NASH_CASCADE for Nash Cascade; default is GIUH, version 1 is GIUH, Version 2 is Nash",
)
is_sft_coupled: bool = Field(
    False,
    description="Optional. Turns on/off the CFE coupling with the SoilFreezeThaw. If this parameter is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then ice_content_threshold also needs to be defined in the config file.",
)
ice_content_threshold: FloatWithUnits | None = Field(
    default=FloatWithUnits(value=CFEValues.ICE_CONTENT_THR.value, units=CFEUnits.ICE_CONTENT_THR.value),
    description="Optional. This represents the ice content above which soil is impermeable. If this is_sft_couple is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then this also needs to be defined in the config file.",
)
soil_params_b: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_B.value, units=CFEUnits.SOIL_B.value),
    description="Beta exponent on Clapp-Hornberger (1978) soil water relations",
    serialization_alias="b",
)
soil_params_satdk: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_SATDK.value, units=CFEUnits.SOIL_SATDK.value),
    description="Saturated hydraulic conductivity",
    serialization_alias="satdk",
)
soil_params_satpsi: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_SATPSI.value, units=CFEUnits.SOIL_SATPSI.value),
    description="Saturated capillary head",
    serialization_alias="satpsi",
)
soil_params_slop: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_SLOP.value, units=CFEUnits.SOIL_SLOP.value),
    description="This factor (0-1) modifies the gradient of the hydraulic head at the soil bottom.  0=no-flow.",
    serialization_alias="slope",
)
soil_params_smcmax: FloatWithUnits = Field(
    default=FloatWithUnits(
        value=CFEValues.SOIL_SMCMAX.value,
        units=CFEUnits.SOIL_SMCMAX.value,
    ),
    description="Saturated soil moisture content (Maximum soil moisture content)",
    serialization_alias="maxsmc",
)
soil_params_wltsmc: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_WLTSMC.value, units=CFEUnits.SOIL_WLTSMC.value),
    description="Wilting point soil moisture content (< soil_params.smcmax)",
    serialization_alias="wltsmc",
)
soil_params_expon: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_EXPON.value, units=CFEUnits.SOIL_EXPON.value),
    description="Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
    json_schema_extra={"units": "here are units"},
    serialization_alias="soil_params.expon",
)
soil_params_expon_secondary: FloatWithUnits = Field(
    default=FloatWithUnits(
        value=CFEValues.SOIL_EXPON_SECONDARY.value, units=CFEUnits.SOIL_EXPON_SECONDARY.value
    ),
    description="	Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
    serialization_alias="soil_params.expon_secondary",
)
max_gw_storage: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.MAX_GW_STORAGE.value, units=CFEUnits.MAX_GW_STORAGE.value),
    description="Maximum storage in the conceptual reservoir",
)
Cgw: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.CGW.value, units=CFEUnits.CGW.value),
    description="Primary outlet coefficient",
)
expon: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.EXPON.value, units=CFEUnits.EXPON.value),
    description="Exponent parameter for nonlinear ground water reservoir (1.0 for linear reservoir)",
)
gw_storage: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.GW_STORAGE.value, units=CFEUnits.GW_STORAGE.value),
    description="Initial condition for groundwater reservoir - it is the ground water as a decimal fraction of the maximum groundwater storage (max_gw_storage) for the initial timestep",
)
alpha_fc: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.ALPHA_FC.value, units=CFEUnits.ALPHA_FC.value),
    description="Alpha at fc for clapp hornberger (field capacity)",
)
soil_storage: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_STORAGE.value, units=CFEUnits.SOIL_STORAGE.value),
    description="Initial condition for soil reservoir - it is the water in the soil as a decimal fraction of maximum soil water storage (smcmax x depth) for the initial timestep. Default = 0.5",
)
K_nash: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.K_NASH.value, units=CFEUnits.K_NASH.value),
    description="Nash Config param for lateral subsurface runoff (Nash discharge to storage ratio)",
    json_schema_extra={"units": "units"},
    serialization_alias="Kn",
)
K_lf: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.K_LF.value, units=CFEUnits.K_LF.value),
    description="Nash Config param - primary reservoir",
    serialization_alias="Klf",
)
nash_storage: FloatListWithUnits = Field(
    default=FloatListWithUnits(value=CFEValues.NASH_STORAGE.value, units=CFEUnits.NASH_STORAGE.value),
    description="Nash Config param - secondary reservoir",
)
giuh_ordinates: FloatListWithUnits = Field(
    default=FloatListWithUnits(value=CFEValues.GIUH.value, units=CFEUnits.GIUH.value),
    description="Giuh (geomorphological instantaneous unit hydrograph) ordinates in dt time steps",
)
a_Xinanjiang_inflection_point_parameter: FloatWithUnits | None = Field(
    default=FloatWithUnits(
        value=CFEValues.A_XINANJIANG_INFLECT.value, units=CFEUnits.A_XINANJIANG_INFLECT.value
    ),
    description="When surface_water_partitioning_scheme=Xinanjiang",
)
b_Xinanjiang_shape_parameter: FloatWithUnits | None = Field(
    default=FloatWithUnits(
        value=CFEValues.B_XINANJIANG_SHAPE.value, units=CFEUnits.B_XINANJIANG_SHAPE.value
    ),
    description="When surface_water_partitioning_scheme=Xinanjiang",
)
x_Xinanjiang_shape_parameter: FloatWithUnits | None = Field(
    default=FloatWithUnits(
        value=CFEValues.X_XINANJIANG_SHAPE.value, units=CFEUnits.X_XINANJIANG_SHAPE.value
    ),
    description="When surface_water_partitioning_scheme=Xinanjiang",
)
urban_decimal_fraction: FloatWithUnits | None = Field(
    default=FloatWithUnits(value=CFEValues.URBAN_FRACT.value, units=CFEUnits.URBAN_FRACT.value),
    description="When surface_water_partitioning_scheme=Xinanjiang",
)
refkdt: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.REFKDT.value, units=CFEUnits.REFKDT.value),
    description="Reference Soil Infiltration Parameter (used in runoff formulation)",
)
soil_params_depth: FloatWithUnits = Field(
    default=FloatWithUnits(value=CFEValues.SOIL_DEPTH.value, units=CFEUnits.SOIL_DEPTH.value),
    description="Soil depth",
    serialization_alias="soil_params.depth",
)
is_aet_rootzone: bool = Field(default=CFEValues.IS_AET.value, description="Turn on rootzone AET")
soil_layer_depths: FloatListWithUnits | None = Field(
    default=FloatListWithUnits(
        value=CFEValues.SOIL_LAYER_DEPTHS.value, units=CFEUnits.SOIL_LAYER_DEPTHS.value
    ),
    description="array of depths from the surface for AET",
)
max_rootzone_layer: FloatWithUnits | None = Field(
    default=FloatWithUnits(
        value=CFEValues.MAX_ROOTZONE_LAYER.value, units=CFEUnits.MAX_ROOTZONE_LAYER.value
    ),
    description="layer of the soil that is the maximum root zone depth",
)
```

## Usage

### Command Line Interface

The CFE config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "cfe" \
    --domain "conus_hf" \
    --catalog "glue" \
    --cfe-version "CFE-S" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `cfe` for Conceptual Functional Equivalent Model)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--cfe-version`: The CFE module type (`CFE-X`/`CFE-S`)
- `--output`: Output directory for configuration files

### REST API

The CFE module is also accessible via REST API:

```http
GET /v1/modules/cfe/?identifier=01010000&cfe_version=CFE-X
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `cfe_version` (required): The CFE module type (`CFE-X`/`CFE-S`)
- `sft_included` (optional): True if SFT is in the 'dep_modules_included' definition (`True`/`False`; default: `False`)
- `rootzone_aet` (optional): Turn on rootzone based AET (`True`/`False`; default: `False`)

**Response:** Returns a list of CFE configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_cfe_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get CFE parameters
configs = get_cfe_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    cfe_version='CFE-X',
    sft_included=False,
    rootzone_aet=False,
)

# Each config is a CFE pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Surface Water Partitioning Scheme: {config.surface_water_partitioning_scheme}")
    print(f"Surface Runoff Scheme: {config.surface_runoff_scheme}")
    print(f"Is Sft Coupled: {config.is_sft_coupled}")
    print(f"Ice Content Threshold: {config.ice_content_threshold}")
    print(f"Soil Params B: {config.soil_params_b}")
    print("...\n")
```
