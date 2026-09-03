# LSTM (Long Short-Term Memory) Module Documentation

## Overview

The LSTM (Long Short-Term Memory) module was developed as a network for use in NextGen. LSTMs are able to provide relatively accurate streamflow predictions when compared to other model types.

## Parameter Reference

### Core Parameters

| Name          | Datatype | Description                                                                      |
|---------------|----------|----------------------------------------------------------------------------------|
| area_sqkm     | Float    | Allows bmi to adjust a weighted output                                           |
| basin_id      | String   | Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md |
| elev_mean     | Float    | Catchment mean elevation (m) above sea level                                     |
| initial_state | String   | This is an option to set the initial states of the model to zero.                |
| lat           | Float    | Latitude                                                                         |
| lon           | Float    | Longitude                                                                        |
| slope_mean    | Float    | Catchment mean slope (m km−1)                                                    |

## Data Structures

### LSTM Configuration Model

The LSTM module uses a Pydantic model to validate and structure configuration parameters:

```python
area_sqkm: float = Field(..., description="Allows bmi to adjust a weighted output")
basin_id: str = Field(
    ..., description="Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md"
)
elev_mean: float = Field(..., description="Catchment mean elevation (m) above sea level")
initial_state: str = Field(
    default="zero", description="This is an option to set the initial states of the model to zero."
)
lat: float = Field(..., description="Latitude")
lon: float = Field(..., description="Longitude")
slope_mean: float = Field(..., description="Catchment mean slope (m km−1)")
```

## Usage

### Command Line Interface

The LSTM config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "lstm" \
    --domain "conus_hf" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `lstm` for Long Short-Term Memory)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The LSTM module is also accessible via REST API:

```http
GET /v1/modules/lstm/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.

**Response:** Returns a list of LSTM configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_lstm_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get LSTM parameters
configs = get_lstm_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000"
)

# Each config is an LSTM pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Area SQKM: {config.area_sqkm}")
    print(f"Basin ID: {config.basin_id}")
    print(f"Elev Mean: {config.elev_mean}")
    print(f"Initial State: {config.initial_state}")
    print(f"Lat: {config.lat}")
    print(f"...\n")
```
