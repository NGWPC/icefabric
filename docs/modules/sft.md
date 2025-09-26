# SFT (Soil Freeze-Thaw) Module Documentation

## Overview

The SFT (Soil Freeze-Thaw) module simulates the freeze-thaw processes in soil columns and is used in cold regions where freeze-thaw cycles significantly affect water movement and storage.

## Parameter Reference

### Core Parameters

| Parameter | Description | Units | Data Type | Default | Calibratable |
|-----------|-------------|--------|-----------|---------|--------------|
| `end_time` | Simulation duration. If no unit is specified, defaults to hour | s, sec, h, hr, d, day | double | `1.[d]` | FALSE |
| `dt` | Size of a simulation timestep. If no unit is specified, defaults to hour | s, sec, h, hr, d, day | double | `1.0[h]` | FALSE |
| `verbosity` | Logging verbosity level | - | string | `none` | FALSE |

**Options for verbosity:** `high`, `low`, `none`

### Soil Physical Properties

These properties are based on Hydrofabric divide attributes provided in the latest enterprise version.

| Parameter | Description | Units | Data Type | Default | Calibratable |
|-----------|-------------|--------|-----------|---------|--------------|
| `soil_params.smcmax` | Maximum soil moisture content | - | double | - | TRUE |
| `soil_params.b` | Soil moisture retention curve parameter (bexp) | - | double | - | TRUE |
| `soil_params.satpsi` | Saturated soil suction (psisat) | - | double | - | TRUE |
| `soil_params.quartz` | Soil quartz content, used in soil thermal conductivity function of Peters-Lidard | - | double | `1.0` | FALSE |

### Domain Configuration

| Parameter | Description | Units | Data Type | Default | Calibratable |
|-----------|-------------|--------|-----------|---------|--------------|
| `soil_z` | Vertical resolution of the soil column (computational domain of the SFT model) | m | array[double] | `[0.1, 0.3, 1.0, 2.0]` | FALSE |
| `soil_temperature` | Initial soil temperature for the discretized column | K | array[double] | - | FALSE |

**Ice Fraction Scheme Options:**

The following ice fraction schemes are dictated by what version of CFE is used

- `Schaake`: Traditional Schaake ice fraction calculation
- `Xinanjiang`: Xinanjiang ice fraction calculation method (default)

## Data Structures

### SFT Configuration Model

The SFT module uses a Pydantic model to validate and structure configuration parameters:

```python
class SFT(BaseModel):
    catchment: str = Field(..., description="The catchment ID")
    verbosity: str = Field(default="none", description="Verbosity level")
    soil_moisture_bmi: int = Field(default=1, description="Soil moisture BMI parameter")
    end_time: str = Field(default="1.[d]", description="End time with units")
    dt: str = Field(default="1.0[h]", description="Time step with units")
    soil_params_smcmax: float = Field(..., description="Maximum soil moisture content", alias="smcmax")
    soil_params_b: float = Field(..., description="Soil moisture retention curve parameter (bexp)", alias="b")
    soil_params_satpsi: float = Field(..., description="Saturated soil suction (psisat)", alias="satpsi")
    soil_params_quartz: float = Field(default=1.0, description="Quartz content", alias="quartz")
    ice_fraction_scheme: IceFractionScheme = Field(..., description="Ice fraction scheme")
    soil_z: list[float] = Field(default=[0.1, 0.3, 1.0, 2.0], description="Soil depth layers in meters")
    soil_temperature: list[float] = Field(..., description="Soil temperature in Kelvin for each layer")
```

### Ice Fraction Schemes

```python
class IceFractionScheme(str, enum.Enum):
    SCHAAKE = "Schaake"
    XINANJIANG = "Xinanjiang"
```

## Usage

### Command Line Interface

The SFT config text files can be created using the `icefabric` CLI tool:

```bash
icefabric params \
    --gauge "01010000" \
    --module "sft" \
    --domain "conus" \
    --catalog "glue" \
    --ice-fraction "xinanjiang" \
    --output "./output"
```

**CLI Parameters:**
- `--gauge`: Gauge ID to trace upstream catchments from
- `--module`: Module type (use "sft" for Soil Freeze-Thaw)
- `--domain`: Hydrofabric domain (`conus`, `alaska`, etc.)
- `--catalog`: PyIceberg Catalog type (`glue` or `sql`)
- `--ice-fraction`: Ice fraction scheme (`schaake` or `xinanjiang`)
- `--output`: Output directory for configuration files

### REST API

The SFT module is also accessible via REST API:

```http
GET /modules/sft/?identifier=01010000&domain=conus&use_schaake=false
```

**API Parameters:**
- `identifier` (required): Gauge ID to trace upstream from
- `domain` (optional): Geographic domain (default: `conus`)
- `use_schaake` (optional): Use Schaake ice fraction scheme (default: `false`)

**Response:** Returns a list of SFT configuration objects, one for each upstream catchment.

### Python API

Direct Python usage:

```python
from icefabric.modules import get_sft_parameters
from icefabric.schemas.hydrofabric import HydrofabricDomains
from pyiceberg.catalog import load_catalog

# Load catalog
catalog = load_catalog("glue")

# Get SFT parameters
configs = get_sft_parameters(
    catalog=catalog,
    namespace=HydrofabricDomains.CONUS,
    identifier="01010000",
    use_schaake=False
)

# Each config is an SFT pydantic model
for config in configs:
    print(f"Catchment: {config.catchment}")
    print(f"Soil layers: {config.soil_z}")
    print(f"Initial temperatures: {config.soil_temperature}")
```

## Parameter Estimation

The system automatically estimates initial parameters from hydrofabric data:

### Soil Parameters
- **smcmax**: Calculated as mean across available soil moisture maximum values
- **b (bexp)**: Derived from mode of soil moisture retention curve parameters
- **satpsi**: Calculated as geometric mean of saturated soil suction values
- **quartz**: Default value of 1.0 (assuming high quartz content)

### Temperature Initialization
- **soil_temperature**: Currently set to a uniform 45°F (280.37K) across all layers
- This represents a reasonable estimate for mean soil temperature

### Spatial Resolution
- **soil_z**: Default 4-layer discretization [0.1, 0.3, 1.0, 2.0] meters
- Provides adequate resolution for freeze-thaw processes

## Output Files

The CLI and API generate BMI-compatible configuration files:

```
{catchment_id}_bmi_config_sft.txt
```

Example file content:
```
verbosity=none
soil_moisture_bmi=1
end_time=1.[d]
dt=1.0[h]
soil_params.smcmax=0.434
soil_params.b=4.05
soil_params.satpsi=0.0355
soil_params.quartz=1.0
ice_fraction_scheme=Xinanjiang
soil_z=0.1,0.3,1.0,2.0[m]
soil_temperature=280.37,280.37,280.37,280.37[K]
```

## Notes and Limitations

1. **Temperature Initialization**: Current implementation uses uniform 45°F across all soil layers. Future versions should implement depth-dependent temperature profiles.

2. **Parameter Weighting**: Soil parameters are currently averaged with equal weighting rather than weighted averaging based on layer thickness.

3. **Quartz Support**: The `soil_params.quartz` was removed in v2.2 of the Hydrofabric and is defaulted to 1.0

4. **Spatial Coverage**: Parameter estimation depends on available hydrofabric data coverage for the specified domain.

5. **Temporal Considerations**: Initial parameters represent steady-state estimates. Actual model runs may require spin-up periods for equilibration.
