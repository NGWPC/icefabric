# UEB Module Documentation

## Overview

The Utah Energy Balance (UEB) snow model is an energy balance snowmelt model developed by David Tarboton's research group, first in 1994.

UEB uses a lumped representation of the snowpack and keeps track of water and energy balance. The model is driven by inputs of air temperature, precipitation, wind speed, humidity and radiation at time steps sufficient to resolve the diurnal cycle (six hours or less). The model uses physically-based calculations of radiative, sensible, latent and advective heat exchanges. Because of its parsimony this model is suitable for application in a distributed fashion on a grid over a watershed.

## Parameter Reference

### Core Parameters

| Name                  | Datatype | Description                                                                                                                                |
|-----------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------|
| aspect                | Float    | Aspect computed from DEM                                                                                                                   |
| slope                 | Float    | Slope                                                                                                                                      |
| longitude             | Float    | X coordinates of divide centroid                                                                                                           |
| latitude              | Float    | Y coordinates of divide centroid                                                                                                           |
| elevation             | Float    | Elevation from DEM                                                                                                                         |
| standard_atm_pressure | Float    | Standard atmospheric pressuure (atm)                                                                                                       |
| jan_temp_range        | Float    | Monthly mean of daily temperature range for January (1)                                                                                    |
| feb_temp_range        | Float    | Monthly mean of daily temperature range for February (2)                                                                                   |
| mar_temp_range        | Float    | Monthly mean of daily temperature range for March(3)                                                                                       |
| apr_temp_range        | Float    | Monthly mean of daily temperature range for April (4)                                                                                      |
| may_temp_range        | Float    | Monthly mean of daily temperature range for May (5)                                                                                        |
| jun_temp_range        | Float    | Monthly mean of daily temperature range for June (6)                                                                                       |
| jul_temp_range        | Float    | Monthly mean of daily temperature range for July (7)                                                                                       |
| aug_temp_range        | Float    | Monthly mean of daily temperature range for August (8)                                                                                     |
| sep_temp_range        | Float    | Monthly mean of daily temperature range for September (9)                                                                                  |
| oct_temp_range        | Float    | Monthly mean of daily temperature range for October (10)                                                                                   |
| nov_temp_range        | Float    | Monthly mean of daily temperature range for November (11)                                                                                  |
| dec_temp_range        | Float    | Monthly mean of daily temperature range for December (12)                                                                                  |
| Usic                  | Float    | Energy content initial condition (kg m-3)                                                                                                  |
| Wsis                  | Float    | Snow water equivalent initial condition (m)                                                                                                |
| Tic                   | Float    | Snow surface dimensionless age initial condition                                                                                           |
| Wcic                  | Float    | Snow water equivalent of canopy condition(m)                                                                                               |
| df                    | Float    | Drift factor multiplier                                                                                                                    |
| Aep                   | Float    | Albedo extinction coefficient                                                                                                              |
| cc                    | Float    | Canopy coverage fraction                                                                                                                   |
| hcan                  | Float    | Canopy height                                                                                                                              |
| lai                   | Float    | Leaf area index                                                                                                                            |
| Sbar                  | Float    | Maximum snow load held per unit branch area                                                                                                |
| ycage                 | Float    | Forest age flag for wind speed profile parameterization                                                                                    |
| subalb                | Float    | Albedo (fraction 0-1) of the substrate beneath the snow (ground, or glacier)                                                               |
| subtype               | Float    | Type of beneath snow substrate (0=Ground/Non Glacier, 1=Clean Ice/glacier, 2=Debris covered ice/glacier, 3=Glacier snow accumulation zone) |
| gsurf                 | Float    | The fraction of surface melt that runs off (e.g. from a glacier                                                                            |
| ts_last               | Float    | Average temperature                                                                                                                        |

## Data Structures

### UEB Configuration Model

The UEB module uses a Pydantic model to validate and structure configuration parameters:

```python
catchment: str | int = Field(..., description="The catchment ID")
aspect: float = Field(..., description="Aspect computed from DEM")
slope: float = Field(..., description="Slope")
longitude: float = Field(..., description="X coordinates of divide centroid")
latitude: float = Field(..., description="Y coordinates of divide centroid")
elevation: float = Field(..., description="Elevation from DEM")
standard_atm_pressure: float = Field(..., description="Standard atmospheric pressuure (atm)")
jan_temp_range: float | None = Field(default=UEBValues.JAN_TEMP.value, description="Average temperature")
feb_temp_range: float | None = Field(default=UEBValues.FEB_TEMP.value, description="Average temperature")
mar_temp_range: float | None = Field(default=UEBValues.MAR_TEMP.value, description="Average temperature")
apr_temp_range: float | None = Field(default=UEBValues.APR_TEMP.value, description="Average temperature")
may_temp_range: float | None = Field(default=UEBValues.MAY_TEMP.value, description="Average temperature")
jun_temp_range: float | None = Field(default=UEBValues.JUN_TEMP.value, description="Average temperature")
jul_temp_range: float | None = Field(default=UEBValues.JUL_TEMP.value, description="Average temperature")
aug_temp_range: float | None = Field(default=UEBValues.AUG_TEMP.value, description="Average temperature")
sep_temp_range: float | None = Field(default=UEBValues.SEP_TEMP.value, description="Average temperature")
oct_temp_range: float | None = Field(default=UEBValues.OCT_TEMP.value, description="Average temperature")
nov_temp_range: float | None = Field(default=UEBValues.NOV_TEMP.value, description="Average temperature")
dec_temp_range: float | None = Field(default=UEBValues.DEC_TEMP.value, description="Average temperature")
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
```

## Usage

### Command Line Interface

The UEB config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "ueb" \
    --domain "conus_hf" \
    --catalog "glue" \
    --envca "False" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `ueb` for Utah Energy Balance Model)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--envca`: Source being ENVCA (`True` or `False`)
- `--output`: Output directory for configuration files

### REST API

The UEB module is also accessible via REST API:

```http
GET /v1/modules/ueb/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `envca` (optional): If source is ENVCA, then set to `True` (default: `False`)

**Response:** Returns a list of UEB configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_ueb_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get UEB parameters
configs = get_ueb_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    envca=False,
)

# Each config is a UEB pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Aspect: {config.aspect}")
    print(f"Slope: {config.slope}")
    print(f"Longitude: {config.longitude}")
    print(f"Latitude: {config.latitude}")
    print(f"Elevation: {config.elevation}")
    print("...\n")
```
