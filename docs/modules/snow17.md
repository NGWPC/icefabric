# SNOW-17 (Snow Accumulation and Ablation Model) Module Documentation

## Overview

The SNOW-17 (Snow Accumulation and Ablation Model) module is a snow accumulation and melt model used for operational streamflow forecasting.

## Parameter Reference

### Core Parameters

| Name     | Datatype | Description                                 |
|----------|----------|---------------------------------------------|
| hru_id   | String   | Unique divide identifier                    |
| hru_area | Float    | Incremental areas of divide                 |
| latitude | Float    | Y coordinates of divide centroid            |
| elev     | Float    | Elevation from DEM                          |
| scf      | Float    | Snow Correction Factor                      |
| mfmax    | Float    | Maximum non-rain melt factor                |
| mfmin    | Float    | Minimum non-rain melt factor                |
| uadj     | Float    | Average wind function for rain on snow      |
| si       | Float    | 100% snow cover threshold                   |
| pxtemp   | Float    | Precipitation vs Snow threshold temperature |
| nmf      | Float    | maximum negative melt factor                |
| tipm     | Float    | Antecedent snow temperature index           |
| mbase    | Float    | Base Temperature for non-rain melt factor   |
| plwhc    | Float    | Percent liquid water holding capacity       |
| daygm    | Float    | Daily ground melt                           |
| adc1     | Float    | areal depletion curve, WE/Ai=0              |
| adc2     | Float    | areal depletion curve, WE/Ai=0.1            |
| adc3     | Float    | areal depletion curve, WE/Ai=0.2            |
| adc4     | Float    | areal depletion curve, WE/Ai=0.3            |
| adc5     | Float    | areal depletion curve, WE/Ai=0.4            |
| adc6     | Float    | areal depletion curve, WE/Ai=0.5            |
| adc7     | Float    | areal depletion curve, WE/Ai=0.6            |
| adc8     | Float    | areal depletion curve, WE/Ai=0.7            |
| adc9     | Float    | areal depletion curve, WE/Ai=0.8            |
| adc10    | Float    | areal depletion curve, WE/Ai=0.9            |
| adc11    | Float    | areal depletion curve, WE/Ai=1.0            |

## Data Structures

### SNOW-17 Configuration Model

The SNOW-17 module uses a Pydantic model to validate and structure configuration parameters:

```python
hru_id: str | int = Field(..., description="Unique divide identifier")
hru_area: float = Field(..., description="Incremental areas of divide")
latitude: float = Field(..., description="Y coordinates of divide centroid")
elev: float = Field(..., description="Elevation from DEM")
scf: float = Field(default=1.100, description="Snow Correction Factor")
mfmax: float = Field(default=1.00, description="Maximum non-rain melt factor")
mfmin: float = Field(default=0.20, description="Minimum non-rain melt factor")
uadj: float = Field(default=0.05, description="Average wind function for rain on snow")
si: float = Field(default=500.00, description="100% snow cover threshold")
pxtemp: float = Field(default=1.000, description="Precipitation vs Snow threshold temperature")
nmf: float = Field(default=0.150, description="maximum negative melt factor")
tipm: float = Field(default=0.100, description="Antecedent snow temperature index")
mbase: float = Field(default=0.000, description="Base Temperature for non-rain melt factor")
plwhc: float = Field(default=0.030, description="Percent liquid water holding capacity")
daygm: float = Field(default=0.000, description="Daily ground melt")
adc1: float = Field(default=0.050, description="areal depletion curve, WE/Ai=0")
adc2: float = Field(default=0.100, description="areal depletion curve, WE/Ai=0.1")
adc3: float = Field(default=0.200, description="areal depletion curve, WE/Ai=0.2")
adc4: float = Field(default=0.300, description="areal depletion curve, WE/Ai=0.3")
adc5: float = Field(default=0.400, description="areal depletion curve, WE/Ai=0.4")
adc6: float = Field(default=0.500, description="areal depletion curve, WE/Ai=0.5")
adc7: float = Field(default=0.600, description="areal depletion curve, WE/Ai=0.6")
adc8: float = Field(default=0.700, description="areal depletion curve, WE/Ai=0.7")
adc9: float = Field(default=0.800, description="areal depletion curve, WE/Ai=0.8")
adc10: float = Field(default=0.900, description="areal depletion curve, WE/Ai=0.9")
adc11: float = Field(default=1.000, description="areal depletion curve, WE/Ai=1.0")
```

## Usage

### Command Line Interface

The SNOW-17 config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "snow17" \
    --domain "conus_hf" \
    --catalog "glue" \
    --envca "False" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `snow17` for Snow Accumulation and Ablation Model)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--envca`: Source being ENVCA (`True` or `False`)
- `--output`: Output directory for configuration files

### REST API

The SNOW-17 module is also accessible via REST API:

```http
GET /v1/modules/snow17/?identifier=01010000&envca=False
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `envca` (optional): If source is ENVCA, then set to `True` (default: `False`)

**Response:** Returns a list of SNOW-17 configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_snow17_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SNOW-17 parameters
configs = get_snow17_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    envca=False
)

# Each config is an SNOW-17 pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"HRU ID: {config.hru_id}")
    print(f"HRU Area: {config.hru_area}")
    print(f"Latitude: {config.latitude}")
    print(f"Elev: {config.elev}")
    print(f"SCF: {config.scf}")
    print(f"...\n")
```
