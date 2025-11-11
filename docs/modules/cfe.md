# CFE Module Documentation

## Overview

CFE (Conceptual Functional Equivalent) is a simplified conceptual model written by Fred Ogden that is designed to be functionally equivalent to the National Water Model.

## Parameter Reference

### Core Parameters

soil_params.depth
soil_params.b
soil_params.satdk
soil_params.satpsi
soil_params.slop
soil_params.smcmax
soil_params.wltsmc
soil_params.expon
soil_params.expon_secondary
max_gw_storage
Cgw
expon
alpha_fc
giuh_ordinates
refkdt
K_nash
K_lf
nash_storage 
surface_water_partitioning_scheme
a_Xinanjiang_inflection_point_parameter
b_Xinanjiang_shape_parameter
x_Xinanjiang_shape_parameter
gw_storage
soil_storage
surface_runoff_scheme
is_aet_rootzone
max_rootzone_layer
soil_layer_depths
is_sft_coupled
ice_content_threshold

## Data Structures

### CFE Configuration Model

The CFE module uses a Pydantic model to validate and structure configuration parameters:

```python
```
catchment: str = Field(..., description="The catchment ID")
    surface_partitioning_scheme: str = Field(..., description="Selects Xinanjiang or Schaake")
    surface_runoff_scheme: str = Field(
        default=CFEValues.SRFC_RUNOFF_SCHEME.value,
        description="Accepts  1 or GIUH for GIUH and  2 or NASH_CASCADE for Nash Cascade; default is GIUH, version 1 is GIUH, Version 2 is Nash",
    )
    is_sft_coupled: bool = Field(
        False,
        description="Optional. Turns on/off the CFE coupling with the SoilFreezeThaw. If this parameter is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then ice_content_threshold also needs to be defined in the config file.",
    )
    ice_content_thresh: float | None = Field(
        default=CFEValues.ICE_CONTENT_THR.value,
        description="Optional. This represents the ice content above which soil is impermeable. If this is_sft_couple is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then this also needs to be defined in the config file.",
    )
    soil_params_b: float = Field(
        default=CFEValues.SOIL_B.value,
        description="Beta exponent on Clapp-Hornberger (1978) soil water relations",
    )
    soil_params_satdk: float = Field(
        default=CFEValues.SOIL_SATDK.value, description="Saturated hydraulic conductivity"
    )
    soil_params_satpsi: float = Field(
        default=CFEValues.SOIL_SATPSI.value, description="Saturated capillary head"
    )
    soil_params_slop: float = Field(
        default=CFEValues.SOIL_SLOP.value,
        description="This factor (0-1) modifies the gradient of the hydraulic head at the soil bottom.  0=no-flow.",
    )
    soil_params_smcmax: float = Field(
        default=CFEValues.SOIL_SMCMAX.value,
        description="Saturated soil moisture content (Maximum soil moisture content)",
    )
    soil_params_wltsmc: float = Field(
        default=CFEValues.SOIL_WLTSMC.value,
        description="Wilting point soil moisture content (< soil_params.smcmax)",
    )
    soil_params_expon: float = Field(
        default=CFEValues.SOIL_EXPON.value,
        description="Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
    )
    soil_params_expon_secondary: float = Field(
        default=CFEValues.SOIL_EXPON_SECONDARY.value,
        description="	Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
    )
    max_gw_storage: float = Field(
        default=CFEValues.MAX_GIUH_STORAGE.value, description="Maximum storage in the conceptual reservoir"
    )
    Cgw: float = Field(default=CFEValues.CGW.value, description="Primary outlet coefficient")
    expon: float = Field(
        default=CFEValues.EXPON.value,
        description="Exponent parameter for nonlinear ground water reservoir (1.0 for linear reservoir)",
    )
    gw_storage: float = Field(
        default=CFEValues.GW_STORAGE.value,
        description="Initial condition for groundwater reservoir - it is the ground water as a decimal fraction of the maximum groundwater storage (max_gw_storage) for the initial timestep",
    )
    alpha_fc: float = Field(
        default=CFEValues.ALPHA_FC.value, description="Alpha at fc for clapp hornberger (field capacity)"
    )
    soil_storage: float = Field(
        default=CFEValues.SOIL_STORAGE.value,
        description="Initial condition for soil reservoir - it is the water in the soil as a decimal fraction of maximum soil water storage (smcmax x depth) for the initial timestep. Default = 0.5",
    )
    K_nash: float = Field(
        default=CFEValues.K_NASH.value,
        description="Nash Config param for lateral subsurface runoff (Nash discharge to storage ratio)",
    )
    K_lf: float = Field(default=CFEValues.K_LF.value, description="Nash Config param - primary reservoir")
    nash_storage: list[float] = Field(
        default=CFEValues.NASH_STORAGE.value, description="Nash Config param - secondary reservoir"
    )
    giuh_ordinates: list[float] = Field(
        default=CFEValues.GIUH.value,
        description="Giuh (geomorphological instantaneous unit hydrograph) ordinates in dt time steps",
    )
    a_Xinanjiang_inflection_point_parameter: float | None = Field(
        ...,
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    b_Xinanjiang_shape_parameter: float | None = Field(
        ...,
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    x_Xinanjiang_shape_parameter: float | None = Field(
        ...,
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    urban_decimal_fraction: float | None = Field(
        ..., description="When surface_water_partitioning_scheme=Xinanjiang"
    )
    refkdt: float = Field(
        default=CFEValues.REFKDT.value,
        description="Reference Soil Infiltration Parameter (used in runoff formulation)",
    )
    soil_params_depth: float = Field(default=CFEValues.SOIL_DEPTH.value, description="Soil depth")
    is_aet_rootzone: bool = Field(default=CFEValues.IS_AET.value, description="Turn on rootzone AET")
    soil_layer_depths: list[float] | None = Field(
        default=CFEValues.SOIL_LAYER_DEPTHS.value, description="array of depths from the surface for AET"
    )
    max_rootzone_layer: float | None = Field(
        default=CFEValues.MAX_ROOTZONE_LAYER.value,
        description="layer of the soil that is the maximum root zone depth",
    )


## Usage

### REST API

The CFE module is also accessible via REST API:

```http
GET /modules/cfe/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `cfe_version`: the CFE module type (e.g. CFE-X, CFE-S)
- `sft_included`: uses SFT (True, False; default: False)
- `rootzone_aet`: Turn on rootzone based AET (True, False; default: False)

**Response:** Returns a list of CFE configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_cfe_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get CFE parameters
configs = get_cfe_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    cfe_version='CFE-X',
    sft_included=True,
    rootzone_aet=True,
)

# Each config is a CFE pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    # TODO - show more
```
