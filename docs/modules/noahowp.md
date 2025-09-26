# Noah-OWP-Modular Module Documentation

## Overview

The Noah-OWP-Modular module is an extended, refactored version of Noah-MP: a land surface model used in many research and operational weather/climate models (e.g., HRLDAS, WRF, MPAS, WRF-Hydro/NWM, NOAA/UFS, NASA/LIS, etc.).

## Parameter Reference

### Core Parameters

TODO

### Soil Physical Properties

TODO

### Domain Configuration

TODO

## Data Structures

### Noah-OWP-Modular Configuration Model

The Noah-OWP-Modular module uses a Pydantic model to validate and structure configuration parameters:

```python
class NoahOwpModular(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    dt: float = Field(default=3600.0, description="Timestep [seconds]")
    startdate: str = Field(default="202408260000", description="UTC time start of simulation (YYYYMMDDhhmm)")
    enddate: str = Field(default="202408260000", description="# UTC time end of simulation (YYYYMMDDhhmm)")
    forcing_filename: str = Field(default=".", description="File containing forcing data")
    output_filename: str = Field(default=".", description="NA")
    parameter_dir: str = Field(default="test", description="NA")
    general_table: str = Field(default="GENPARM.TBL", description="General param tables and misc params")
    soil_table: str = Field(default="SOILPARM.TBL", description="Soil param table")
    noahowp_table: str = Field(default="MPTABLE.TBL", description="Model param tables (includes veg)")
    soil_class_name: str = Field(default="STAS", description="Soil class data source - 'STAS' or 'STAS-RUC'")
    veg_class_name: str = Field(
        default="USGS", description="Vegetation class data source - 'MODIFIED_IGBP_MODIS_NOAH' or 'USGS'"
    )
    lat: float = Field(..., description="Latitude [degrees]  (-90 to 90)")
    lon: float = Field(..., description="Longitude [degrees] (-180 to 180)")
    terrain_slope: float = Field(..., description="Terrain slope [degrees]")
    azimuth: float = Field(..., description="Terrain azimuth or aspect [degrees clockwise from north]")
    ZREF: float = Field(default=10.0, description="Measurement height for wind speed (m)")
    rain_snow_thresh: float = Field(
        default=0.5, description="Rain-snow temperature threshold (degrees Celsius)"
    )
    precip_phase_option: int = Field(default=6, description="NA")
    snow_albedo_option: int = Field(default=1, description="NA")
    dynamic_veg_option: int = Field(default=4, description="NA")
    runoff_option: int = Field(default=3, description="NA")
    drainage_option: int = Field(default=8, description="NA")
    frozen_soil_option: int = Field(default=1, description="NA")
    dynamic_vic_option: int = Field(default=1, description="NA")
    radiative_transfer_option: int = Field(default=3, description="NA")
    sfc_drag_coeff_option: int = Field(default=1, description="NA")
    canopy_stom_resist_option: int = Field(default=1, description="NA")
    crop_model_option: int = Field(default=0, description="NA")
    snowsoil_temp_time_option: int = Field(default=3, description="NA")
    soil_temp_boundary_option: int = Field(default=2, description="NA")
    supercooled_water_option: int = Field(default=1, description="NA")
    stomatal_resistance_option: int = Field(default=1, description="NA")
    evap_srfc_resistance_option: int = Field(default=4, description="NA")
    subsurface_option: int = Field(default=2, description="NA")
    isltyp: float = Field(..., description="Soil texture class")
    nsoil: int = Field(default=4, description="Number of soil levels")
    nsnow: int = Field(default=3, description="Number of snow levels")
    nveg: int = Field(default=27, description="Number of vegetation type")
    vegtyp: int = Field(..., description="Vegetation type")
    croptype: int = Field(
        default=0, description="Crop type (0 = no crops; this option is currently inactive)"
    )
    sfctyp: int = Field(..., description="Land surface type, 1:soil, 2:lake")
    soilcolor: int = Field(default=4, description="Soil color code")
    dzsnso: list[float] = Field(
        default=[0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 1.0], description="Level thickness [m]"
    )
    sice: list[float] = Field(default=[0.0, 0.0, 0.0, 0.0], description="Initial soil ice profile [m3/m3]")
    sh2o: list[float] = Field(default=[0.3, 0.3, 0.3, 0.3], description="Initial soil liquid profile [m3/m3]")
    zwt: int = Field(default=-2.0, description="Initial water table depth below surface [m] ")
```

## Usage

### Command Line Interface

The Noah-OWP-Modular config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "noah_owp" \
    --domain "conus" \
    --catalog "glue" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "noah_owp" for Noah-OWP-Modular)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--output`: Output directory for configuration files

### REST API

The Noah-OWP-Modular module is also accessible via REST API:

```http
GET /modules/noah_owp/?identifier=01010000&domain=conus
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)

**Response:** Returns a list of Noah-OWP-Modular configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_noah_owp_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get Noah-OWP-Modular parameters
configs = get_noah_owp_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000"
)

# Each config is an Noah-OWP-Modular pydantic model
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
{catchment_id}_bmi_config_noah_owp.txt
```

Example file content:
```
# TODO add file content
```

## Notes and Limitations

TODO
