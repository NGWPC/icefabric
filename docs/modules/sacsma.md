# SAC-SMA (Sacramento Soil Moisture Accounting) Module Documentation

## Overview

The SAC-SMA (Sacramento Soil Moisture Accounting) module is a conceptual, continuous, area-lumped model that describes the wetting and drying process in the soil.

## Parameter Reference

### Core Parameters

| Name     | Datatype | Description                                                                       |
|----------|----------|-----------------------------------------------------------------------------------|
| hru_id   | String   | Unique divide identifier                                                          |
| hru_area | Float    | Incremental areas of divide                                                       |
| uztwm    | Float    | Maximum upper zone tension water                                                  |
| uzfwm    | Float    | Maximum upper zone free water                                                     |
| lztwm    | Float    | Maximum lower zone tension water                                                  |
| lzfpm    | Float    | Maximum lower zone free water, primary                                            |
| lzfsm    | Float    | Maximum lower zone free water, secondary                                          |
| adimp    | Float    | Additional 'impervious' area due to saturation                                    |
| uzk      | Float    | Upper zone recession coefficient                                                  |
| lzpk     | Float    | Lower zone recession coefficient, primary                                         |
| lzsk     | Float    | Lower zone recession coefficient, secondary                                       |
| zperc    | Float    | Minimum percolation rate coefficient                                              |
| rexp     | Float    | Percolation equation exponent                                                     |
| pctim    | Float    | Minimum percent impervious area                                                   |
| pfree    | Float    | Percent percolating directly to lower zone free water                             |
| riva     | Float    | Percent of the basin that is riparian area                                        |
| side     | Float    | Portion of the baseflow which does not go to the stream                           |
| rserv    | Float    | Percent of lower zone free water not transferable to the lower zone tension water |

## Data Structures

### SAC-SMA Configuration Model

The SAC-SMA module uses a Pydantic model to validate and structure configuration parameters:

```python
hru_id: str | int = Field(..., description="Unique divide identifier")
hru_area: float = Field(..., description="Incremental areas of divide")
uztwm: float | None = Field(
    default=float(SacSmaValues.UZTWM.value), description="Maximum upper zone tension water"
)
uzfwm: float | None = Field(
    default=float(SacSmaValues.UZFWM.value), description="Maximum upper zone free water"
)
lztwm: float | None = Field(
    default=float(SacSmaValues.LZTWM.value), description="Maximum lower zone tension water"
)
lzfpm: float | None = Field(
    default=float(SacSmaValues.LZFPM.value), description="Maximum lower zone free water, primary"
)
lzfsm: float | None = Field(
    default=float(SacSmaValues.LZFSM.value), description="Maximum lower zone free water, secondary"
)
adimp: float = Field(
    default=float(SacSmaValues.ADIMP.value), description="Additional 'impervious' area due to saturation"
)
uzk: float | None = Field(
    default=float(SacSmaValues.UZK.value), description="Upper zone recession coefficient"
)
lzpk: float | None = Field(
    default=float(SacSmaValues.LZPK.value), description="Lower zone recession coefficient, primary"
)
lzsk: float | None = Field(
    default=float(SacSmaValues.LZSK.value), description="Lower zone recession coefficient, secondary"
)
zperc: float | None = Field(
    default=float(SacSmaValues.ZPERC.value), description="Minimum percolation rate coefficient"
)
rexp: float | None = Field(
    default=float(SacSmaValues.REXP.value), description="Percolation equation exponent"
)
pctim: float = Field(
    default=float(SacSmaValues.PCTIM.value), description="Minimum percent impervious area"
)
pfree: float | None = Field(
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
    --nwm-module "sacsma" \
    --domain "conus_hf" \
    --catalog "glue" \
    --envca "False" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--nwm-module`: Module type (use `sacsma` for Sacramento Soil Moisture Accounting)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--envca`: Source being ENVCA (`True` or `False`)
- `--output`: Output directory for configuration files

### REST API

The SAC-SMA module is also accessible via REST API:

```http
GET /v1/modules/sacsma/?identifier=01010000&envca=False
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.
- `envca` (optional): If source is ENVCA, then set to `True` (default: `False`)

**Response:** Returns a list of SAC-SMA configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_sacsma_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SAC-SMA parameters
configs = get_sacsma_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000",
    envca=False
)

# Each config is an SAC-SMA pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"HRU ID: {config.hru_id}")
    print(f"HRU Area: {config.hru_area}")
    print(f"Uztwm: {config.uztwm}")
    print(f"Uzfwm: {config.uzfwm}")
    print(f"Lztwm: {config.lztwm}")
    print(f"...\n")
```
