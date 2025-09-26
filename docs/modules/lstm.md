# LSTM (Long Short-Term Memory) Module Documentation

## Overview

The LSTM (Long Short-Term Memory) module was developed as a network for use in NextGen. LSTMs are able to provide relatively accurate streamflow predictions when compared to other model types.

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### LSTM Configuration Model

The LSTM module uses a Pydantic model to validate and structure configuration parameters:

```python
class LSTM(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    area_sqkm: float = Field(..., description="Allows bmi to adjust a weighted output")
    basin_id: str = Field(
        ..., description="Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md"
    )
    basin_name: str = Field(
        default="",
        description="Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md",
    )
    elev_mean: float = Field(..., description="Catchment mean elevation (m) above sea level")
    inital_state: str = Field(
        default="zero", description="This is an option to set the initial states of the model to zero."
    )
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    slope_mean: float = Field(..., description="Catchment mean slope (m km−1)")
    timestep: str = Field(
        default="1 hour",
        description="Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md",
    )
    train_cfg_file: str = Field(
        default="",
        description="This is a configuration file used when training the model. It has critical information on the LSTM architecture and should not be altered.",
    )
    verbose: str = Field(
        default="0", description="Change to 1 in order to print additional BMI information during runtime."
    )
```

## Usage

### Command Line Interface

The LSTM config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "lstm" \
    --domain "conus" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "lstm" for Long Short-Term Memory)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The LSTM module is also accessible via REST API:

```http
GET /modules/lstm/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)

**Response:** Returns a list of LSTM configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_lstm_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get LSTM parameters
configs = get_lstm_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000"
)

# Each config is an LSTM pydantic model
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
{catchment_id}_bmi_config_lstm.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
