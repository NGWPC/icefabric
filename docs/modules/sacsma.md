# SAC-SMA (Sacramento Soil Moisture Accounting) Module Documentation

## Overview

The SAC-SMA (Sacramento Soil Moisture Accounting) module is a conceptual, continuous, area-lumped model that describes the wetting and drying process in the soil.

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### SAC-SMA Configuration Model

The SAC-SMA module uses a Pydantic model to validate and structure configuration parameters:

```python
class SacSma(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    hru_id: str = Field(..., description="Unique divide identifier")
    hru_area: float = Field(..., description="Incremental areas of divide")
    uztwm: float = Field(
        default=float(SacSmaValues.UZTWM.value), description="Maximum upper zone tension water"
    )
    uzfwm: float = Field(default=float(SacSmaValues.UZFWM.value), description="Maximum upper zone free water")
    lztwm: float = Field(
        default=float(SacSmaValues.LZTWM.value), description="Maximum lower zone tension water"
    )
    lzfpm: float = Field(
        default=float(SacSmaValues.LZFPM.value), description="Maximum lower zone free water, primary"
    )
    lzfsm: float = Field(
        default=float(SacSmaValues.LZFSM.value), description="Maximum lower zone free water, secondary"
    )
    adimp: float = Field(
        default=float(SacSmaValues.ADIMP.value), description="Additional 'impervious' area due to saturation"
    )
    uzk: float = Field(default=float(SacSmaValues.UZK.value), description="Upper zone recession coefficient")
    lzpk: float = Field(
        default=float(SacSmaValues.LZPK.value), description="Lower zone recession coefficient, primary"
    )
    lzsk: float = Field(
        default=float(SacSmaValues.LZSK.value), description="Lower zone recession coefficient, secondary"
    )
    zperc: float = Field(
        default=float(SacSmaValues.ZPERC.value), description="Minimum percolation rate coefficient"
    )
    rexp: float = Field(default=float(SacSmaValues.REXP.value), description="Percolation equation exponent")
    pctim: float = Field(
        default=float(SacSmaValues.PCTIM.value), description="Minimum percent impervious area"
    )
    pfree: float = Field(
        default=float(SacSmaValues.PFREE.value),
        description="Percent percolating directly to lower zone free water",
    )
    riva: float = Field(
        default=float(SacSmaValues.RIVA.value), description="Percent of the basin that is riparian area"
    )
    side: float = Field(
        default=float(SacSmaValues.SIDE.value),
        description="Portion of the baseflow which does not go to the stream",
    )
    rserv: float = Field(
        default=float(SacSmaValues.RSERV.value),
        description="Percent of lower zone free water not transferable to the lower zone tension water",
    )
```

## Usage

### Command Line Interface

The SAC-SMA config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "sacsma" \
    --domain "conus" \
    --catalog "glue" \
    --envca "False" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "sacsma" for Sacramento Soil Moisture Accounting)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--envca`: Source being ENVCA (True or False)
- `--output`: Output directory for configuration files

### REST API

The SAC-SMA module is also accessible via REST API:

```http
GET /modules/sacsma/?identifier=01010000&domain=conus&envca=False
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `envca` (optional): If source is ENVCA, then set to True (default: `false`)

**Response:** Returns a list of SAC-SMA configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_sacsma_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SAC-SMA parameters
configs = get_sacsma_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    envca=False
)

# Each config is an SAC-SMA pydantic model
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
{catchment_id}_bmi_config_sacsma.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
