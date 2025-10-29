# Topoflow Module Documentation

## Overview

A glacier energy balance module as part of TopoFlow, an open source, BMI compatible, modularized, distributed hydrologic model in Python.

## Parameter Reference

### Core Parameters

da: drainage area
slope: terrain slope in degrees
aspect: terrain aspect in degrees
lat: Y coordinates of divide centroid
lon: X coordinates of divide centroid
elev: Elevation from DEM
h_active_layer:
h0_snow:
h0_ice:
h0_swe:
h0_iwe:
T_rain_snow:
glacier_percent:  percentage of catchment that is glaciated

## Data Structures

### Topoflow Configuration Model

The Topoflow module uses a Pydantic model to validate and structure configuration parameters:

```python
```
class Topoflow(BaseModel):
    """Pydantic model for Topoflow module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    site_prefix: str = Field(..., description="The catchment ID")
    forcing_file: str = Field(...,description="forcing file name")
    dt: int = Field(default=1,description="timestep")
    start_time: str = Field(default="2013032000",description="start time")
    end_time: str = Field(default="2013052000",description="end time")
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


## Usage

### REST API

The Topoflow module is also accessible via REST API:

```http
GET /modules/topoflow/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)

**Response:** Returns a list of Topoflow configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_topoflow_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get Topoflow parameters
configs = get_topoflow_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000"
)

# Each config is a Topoflow pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    # TODO - show more
```

## Output Files

The CLI and API generate BMI-compatible configuration files:

```
{catchment_id}_bmi_config_topoflow.txt
