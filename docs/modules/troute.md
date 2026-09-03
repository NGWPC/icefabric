# T-Route (Tree-Based Channel Routing) Module Documentation

## Overview

The T-Route (Tree-Based Channel Routing) module is a dynamic channel routing model, which offers a comprehensive solution for river network routing problems. It is designed to handle 1-D channel routing challenges in vector-based river network data

## Parameter Reference

### Core Parameters

| Name                        | Datatype   | Description                 |
|-----------------------------|------------|-----------------------------|
| bmi_parameters              | Dictionary | BMI Parameters              |
| log_param                   | Dictionary | Log Parameters              |
| network_topology_parameters | Dictionary | Network Topology Parameters |
| compute_parameters          | Dictionary | Compute Parameters          |
| output_parameters           | Dictionary | Output Parameters           |

## Data Structures

### T-Route Configuration Model

The T-Route module uses a Pydantic model to validate and structure configuration parameters:

```python
class TRoute(BaseModel):
bmi_parameters: dict = Field(default=bmi_parameters, description="BMI Parameters")
log_param: dict = Field(default=log_param, description="Log Parameters")
network_topology_parameters: dict = Field(
    default=network_topology_parameters, description="Network Topology Parameters"
)
compute_parameters: dict = Field(default=compute_parameters, description="Compute Parameters")
output_parameters: dict = Field(default=output_parameters, description="Output Parameters")
```

Its defaults are defined in the model as well:

```python
bmi_parameters = {
    "flowpath_columns": ["id", "toid", "lengthkm"],
    "attributes_columns": [
        "attributes_id",
        "gage",
        "WaterbodyID",
        "MusK",
        "MusX",
        "n",
        "So",
        "ChSlp",
        "BtmWdth",
        "nCC",
        "TopWdthCC",
        "TopWdth",
    ],
    "waterbody_columns": [
        "hl_link",
        "ifd",
        "LkArea",
        "LkMxE",
        "OrificeA",
        "OrificeC",
        "OrificeE",
        "WeirC",
        "WeirE",
        "WeirL",
    ],
    "network_columns": ["network_id", "hydroseq", "hl_uri"],
}

log_param = {"showtiming": True, "log_level": "DEBUG"}

network_topology_parameters = {
    "supernetwork_parameters": {
        "network_type": "HYFeaturesNetwork",
        "geo_file_path": "",
        "columns": ntwk_columns,
        "duplicate_wb_segments": dupseg,
    },
    "waterbody_parameters": {
        "break_network_at_waterbodies": True,
        "level_pool": {"level_pool_waterbody_parameter_file_path": ""},
    },
}

compute_parameters = {
    "parallel_compute_method": "by-subnetwork-jit-clustered",
    "subnetwork_target_size": 10000,
    "cpu_pool": 16,
    "compute_kernel": "V02-structured",
    "assume_short_ts": True,
    "restart_parameters": {"start_datetime": ""},
    "forcing_parameters": {
        "qts_subdivisions": 12,
        "dt": 300,
        "qlat_input_folder": ".",
        "qlat_file_pattern_filter": "nex-*",
        "nts": 5,
        "max_loop_size": divmod(5 * 300, 3600)[0] + 1,
    },
    "data_assimilation_parameters": {
        "usgs_timeslices_folder": None,
        "usace_timeslices_folder": None,
        "timeslice_lookback_hours": 48,
        "qc_threshold": 1,
        "streamflow_da": stream_da,
        "reservoir_da": reservoir_da,
    },
}

output_parameters = {
    "stream_output": {
        "stream_output_directory": ".",
        "stream_output_time": divmod(5 * 300, 3600)[0] + 1,
        "stream_output_type": ".nc",
        "stream_output_internal_frequency": 60,
    }
}
```

These defaults are informed by the following dictionary definitions:

```python
reservoir_da: ClassVar[dict] = {
    "reservoir_persistence_da": {
        "reservoir_persistence_usgs": False,
        "reservoir_persistence_usace": False,
    },
    "reservoir_rfc_da": {
        "reservoir_rfc_forecasts": False,
        "reservoir_rfc_forecasts_time_series_path": None,
        "reservoir_rfc_forecasts_lookback_hours": 28,
        "reservoir_rfc_forecasts_offset_hours": 28,
        "reservoir_rfc_forecast_persist_days": 11,
    },
    "reservoir_parameter_file": None,
}

stream_da: ClassVar[dict] = {
    "streamflow_nudging": False,
    "diffusive_streamflow_nudging": False,
    "gage_segID_crosswalk_file": None,
}

dupseg: ClassVar[list] = [
    "717696",
    "1311881",
    "3133581",
    "1010832",
    "1023120",
    "1813525",
    "1531545",
    "1304859",
    "1320604",
    "1233435",
    "11816",
    "1312051",
    "2723765",
    "2613174",
    "846266",
    "1304891",
    "1233595",
    "1996602",
    "2822462",
    "2384576",
    "1021504",
    "2360642",
    "1326659",
    "1826754",
    "572364",
    "1336910",
    "1332558",
    "1023054",
    "3133527",
    "3053788",
    "3101661",
    "2043487",
    "3056866",
    "1296744",
    "1233515",
    "2045165",
    "1230577",
    "1010164",
    "1031669",
    "1291638",
    "1637751",
]

ntwk_columns: ClassVar[dict] = {
    "key": "id",
    "downstream": "toid",
    "dx": "lengthkm",
    "n": "n",
    "ncc": "nCC",
    "s0": "So",
    "bw": "BtmWdth",
    "waterbody": "WaterbodyID",
    "gages": "gage",
    "tw": "TopWdth",
    "twcc": "TopWdthCC",
    "musk": "MusK",
    "musx": "MusX",
    "cs": "ChSlp",
    "alt": "alt",
}
```

## Usage

### Command Line Interface

The T-Route config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --nwm-module "troute" \
    --domain "conus_hf" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**

- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use `troute` for Tree-Based Channel Routing)
- `--domain`: Hydrofabric domain (`conus_hf`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The T-Route module is also accessible via REST API:

```http
GET /v1/modules/troute/?identifier=01010000
```

**API Parameters:**

- `identifier` (required): Gage ID from which to trace upstream catchments.
- `source` (optional): `nhf` (National Hydrofabric) or `hf` (Hydrofabric v2.2). Required when using geographic domain names.
- `domain` (optional): Geographic domain (`CONUS`, `Alaska`, `Hawaii`, `Puerto_Rico`, `Great_Lakes`) with source param, or legacy values (`nhf`, `conus_hf`, etc.) for backwards compatibility.

**Response:** Returns a list of T-Route configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_troute_parameters
from icefabric.schemas.hydrofabric import HydrofabricNamespace
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get T-Route parameters
configs = get_troute_parameters(
    catalog=catalog,
    namespace=HydrofabricNamespace.CONUS_NHF,
    identifier="01010000"
)

# Each config is an T-Route pydantic model
for config in configs:
    print(f"BMI Parameters: {config.bmi_parameters}")
    print(f"Log Param: {config.log_param}")
    print(f"Network Topology Parameters: {config.network_topology_parameters}")
    print(f"...\n")
```
