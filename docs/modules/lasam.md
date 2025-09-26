# LASAM (Lumped Arid/Semi-arid Model) Module Documentation

## Overview

The LASAM (Lumped Arid/Semi-arid Model) module simulates infiltration and runoff based on Layered Green & Ampt with redistribution (LGAR) model. LGAR is a model which partitions precipitation into infiltration and runoff, and is designed for use in arid or semi-arid climates.

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### LASAM Configuration Model

The LASAM module uses a Pydantic model to validate and structure configuration parameters:

```python
class LASAM(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    verbosity: str = Field(default="none", description="NA")
    soil_params_file: str = Field(..., description="Full path to vG_default_params.dat")
    layer_thickness: str = Field(default="200.0[cm]", description="Thickness of each layer (array)")
    initial_psi: str = Field(default="2000.0[cm]", description="NA")
    timestep: str = Field(default="300[sec]", description="NA")
    endtime: str = Field(default="1000[hr]", description="NA")
    forcing_resolution: str = Field(default="3600[sec]", description="NA")
    ponded_depth_max: str = Field(
        default="1.1[cm]",
        description="Maximum amount of ponded water that is allowed to accumulate on the soil surface",
    )
    use_closed_form_G: bool = Field(default=False, description="NA")
    layer_soil_type: float = Field(default="", description="Type of each soil layer (array)")
    max_soil_types: int = Field(default=15, description="NA")
    wilting_point_psi: str = Field(
        default="15495.0[cm]", description="Wilting point (the amount of water not available for plants)"
    )
    field_capacity_psi: str = Field(
        default="340.9[cm]",
        description="Capillary head corresponding to volumetric water content at which gravity drainage becomes slower",
    )
    giuh_ordinates: list[float] = Field(default=[0.06, 0.51, 0.28, 0.12, 0.03], description="giuh")
    calib_params: bool = Field(default=True, description="NA")
    adaptive_timestep: bool = Field(default=True, description="NA")
    sft_coupled: bool = Field(..., description="NA")
    soil_z: list[float] = Field(default=[10, 30, 100.0, 200.0], description="NA")
```

## Usage

### Command Line Interface

The LASAM config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "lasam" \
    --domain "conus" \
    --catalog "glue" \
    --sft-included "False" \
    --soil-params-file "vG_default_params_HYDRUS.dat" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "lasam" for Lumped Arid/Semi-arid Model)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--sft-included`: Denotes that SFT is in the "dep_modules_included" definition as declared in the HF API repo (`True`/`False`, defaults to `False`)
- `--soil-params-file`: Name of the Van Genuchton soil parameters file (defaults to `vG_default_params_HYDRUS.dat`)
- `--output`: Output directory for configuration files

### REST API

The LASAM module is also accessible via REST API:

```http
GET /modules/lasam/?identifier=01010000&domain=conus&sft_included=false&soil_params_file=vG_default_params_HYDRUS.dat
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `sft_included` (optional): True if SFT is in the "dep_modules_included" definition as declared in HF API repo
- `soil_params_file` (optional): Name of the Van Genuchton soil parameters file. Note: This is the filename that gets returned by HF API's utility script get_hydrus_data()

**Response:** Returns a list of LASAM configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_lasam_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get LASAM parameters
configs = get_lasam_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    sft_included="False",
    soil_params_file="vG_default_params_HYDRUS.dat"
)

# Each config is an LASAM pydantic model
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
{catchment_id}_bmi_config_lasam.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
