# UEB Module Documentation

## Overview

Utah Energy Balance snowmelt model.

## Parameter Reference

### Core Parameters

USic:  Energy content initial condition (kg m-3)
WSis:  Snow water equivalent initial condition (m)
Tic:  Snow surface dimensionless age initial condition
WCic:  Snow water equivalent of canopy condition(m)
df: Drift factor multiplier
apr: Average atmospheric pressure
Aep: Albedo extinction coefficient
cc: Canopy coverage fraction
hcan: Canopy height
lai: Leaf area index
Sbar: Maximum snow load held per unit branch area
ycage: Forest age flag for wind speed profile parameterization
slope: A 2-D grid that contains the slope at each grid point
aspect: A 2-D grid that contains the aspect at each grid point
latitude: A 2-D grid that contains the latitude at each grid point
subalb: Albedo (fraction 0-1) of the substrate beneath the snow (ground, or glacier)
subtype: Type of beneath snow substrate encoded as (0 = Ground/Non Glacier, 1=Clean Ice/glacier, 2= Debris covered ice/glacier, 3= Glacier snow accumulation zone)

gsurf: The fraction of surface melt that runs off (e.g. from a glacier)
b01: Bristow-Campbell B for January (1)
b02: Bristow-Campbell B for February (2)
b03: Bristow-Campbell B for March(3)
b04: Bristow-Campbell B for April (4)
b05: Bristow-Campbell B for may (5)
b06: Bristow-Campbell B for June (6)
b07: Bristow-Campbell B for July (7)
b08:  Bristow-Campbell B for August (8)
b09: Bristow-Campbell B for September (9)
b10: Bristow-Campbell B for October (10)
b11: Bristow-Campbell B for November (11)
b12: Bristow-Campbell B for December (12)
ts_last:  degree celsius
longitude: A 2-D grid that contains the longitude at each grid

## Data Structures

### UEB Configuration Model

The UEB module uses a Pydantic model to validate and structure configuration parameters:

```python
```
    catchment: str = Field(..., description="The catchment ID")
    aspect: float = Field(..., description="Aspect computed from DEM")
    slope: float = Field(..., description="Slope")
    longitude: float = Field(..., description="X coordinates of divide centroid")
    latitude: float = Field(..., description="Y coordinates of divide centroid")
    elevation: float = Field(..., description="Elevation from DEM")
    standard_atm_pressure: float = Field(..., description="Standard atmospheric pressuure (atm)")
    jan_temp_range: float = Field(default=UEBValues.JAN_TEMP.value, description="Average temperature")
    feb_temp_range: float = Field(default=UEBValues.FEB_TEMP.value, description="Average temperature")
    mar_temp_range: float = Field(default=UEBValues.MAR_TEMP.value, description="Average temperature")
    apr_temp_range: float = Field(default=UEBValues.APR_TEMP.value, description="Average temperature")
    may_temp_range: float = Field(default=UEBValues.MAY_TEMP.value, description="Average temperature")
    jun_temp_range: float = Field(default=UEBValues.JUN_TEMP.value, description="Average temperature")
    jul_temp_range: float = Field(default=UEBValues.JUL_TEMP.value, description="Average temperature")
    aug_temp_range: float = Field(default=UEBValues.AUG_TEMP.value, description="Average temperature")
    sep_temp_range: float = Field(default=UEBValues.SEP_TEMP.value, description="Average temperature")
    oct_temp_range: float = Field(default=UEBValues.OCT_TEMP.value, description="Average temperature")
    nov_temp_range: float = Field(default=UEBValues.NOV_TEMP.value, description="Average temperature")
    dec_temp_range: float = Field(default=UEBValues.DEC_TEMP.value, description="Average temperature")
    Usic: float = Field(default=UEBValues.USIC.value, description="Energy content initial condition (kg m-3)")
    Wsis: float = Field(
        default=UEBValues.WSIS.value, description="Snow water equivalent initial condition (m)"
    )
    Tic: float = Field(
        default=UEBValues.TIC.value, description="Snow surface dimensionless age initial condition"
    )
    Wcic: float = Field(
        default=UEBValues.WCIC.value, description="Snow water equivalent of canopy condition(m)"
    )
    df: float = Field(default=UEBValues.DF.value, description="Drift factor multiplier")
    Aep: float = Field(default=UEBValues.AEP.value, description="Albedo extinction coefficient")
    cc: float = Field(default=UEBValues.CC.value, description="Canopy coverage fraction")
    hcan: float = Field(default=UEBValues.HCAN.value, description="Canopy height")
    lai: float = Field(default=UEBValues.LAI.value, description="Leaf area index")
    Sbar: float = Field(
        default=UEBValues.SBAR.value, description="Maximum snow load held per unit branch area"
    )
    ycage: float = Field(
        default=UEBValues.YCAGE.value, description="Forest age flag for wind speed profile parameterization"
    )
    subalb: float = Field(
        default=UEBValues.SUBALB.value,
        description="Albedo (fraction 0-1) of the substrate beneath the snow (ground, or glacier)",
    )
    subtype: float = Field(
        default=UEBValues.SUBTYPE.value,
        description="Type of beneath snow substrate encoded as (0 = Ground/Non Glacier, 1=Clean"
        " Ice/glacier, 2= Debris covered ice/glacier, 3= Glacier snow accumulation zone",
    )
    gsurf: float = Field(
        default=UEBValues.GSURF.value,
        description="The fraction of surface melt that runs off (e.g. from a glacier",
    )
    ts_last: float = Field(default=UEBValues.TS_LAST.value, description="Average temperature")
## Usage

### REST API

The UEB module is also accessible via REST API:

```http
GET /modules/ueb/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `envca` (optional):  If ENVCA (True, False; default is False)

**Response:** Returns a list of UEB configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_ueb_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get UEB parameters
configs = get_ueb_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    envca=False,
)

# Each config is a UEB pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    # TODO - show more
```
