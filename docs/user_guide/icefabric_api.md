# Icefabric API Guide

## Overview

The Icefabric API is a FastAPI-based service that provides access to EDFS data stored in Apache Iceberg format. The API offers multiple data export formats and metadata endpoints for the hydrofabric and streamflow observations.

## Architecture

The API consists of several key components:

1. **Main Application** (`app/main.py`) - FastAPI application with health checks and router configuration
2. **Data Routers** - Handles all data endpoints. Streamflow observations, Hydrofabric subsetting, National Water Model module configuration, and HEC-RAS cross-section retrieval are supported.
3. **Apache Iceberg Backend** - Defaults to hosted AWS Glue catalog. Local SQLite-backed catalog may be built using instructions below.

### Running the API locally
To run the API locally, ensure your `.env` file in your project root has the right credentials (`test`), then run
```sh
uv sync
source .venv/bin/activate
python -m app.main
```
This should spin up the API services at `localhost:8000/`

### Building the API through Docker
To run the API locally with Docker, ensure your `.env` file in your project root has the right credentials, then run
```sh
docker compose -f docker/compose.yaml build --no-cache
docker compose -f docker/compose.yaml up
```
This should spin up the API services

### Running the API with a local Iceberg catalog - Advanced Use
To run the API locally against a local catalog, the catalog must first be exported from glue. In the following code block, run build script for as many catalog namespaces as you need. Ensure your `.env` file in your project root has the right credentials (`test`), then run
```sh
uv sync
source .venv/bin/activate
python tools/pyiceberg/export_catalog.py --namespace conus_hf
# Run additional tool times with other namespaces as necessary
```

To view the namespaces hosted on glue, you can run the following commands in the terminal:
```python
>>> from pyiceberg.catalog import load_catalog
>>> catalog = load_catalog("glue")
>>> catalog.list_namespaces()
```


To run the API locally with a local SQL backend, ensure your `.env` file in your project root has the right credentials (`test`), then run
```sh
uv sync
source .venv/bin/activate
python -m app.main --catalog sql
```
This should spin up the API services

## How It Works

### Data Flow

1. **Request Processing** - Validates data source and identifier parameters
2. **Data Filtering** - Applies optional date range filters to Iceberg tables
3. **Format Conversion** - Exports data in requested format (CSV/Parquet)
4. **Response Generation** - Returns data with appropriate headers and metadata

### Supported Data Sources

#### Observations
Currently supports:

- **USGS** - United States Geological Survey hourly streamflow data

#### Hydrofabric
Provides geospatial watershed data:

- **Subset Generation** - Creates upstream watershed subsets from identifiers

!!! note "Data Storage"
    All data is stored remotely as Apache Iceberg tables on AWS glue unless you built the catalog locally. Then, it is stored at SQLite-backed catalog locally built at `/tmp/warehouse/pyiceberg_catalog.db`

### National Water Model Modules
Retrieve National Water Model (NWM) module parameters.

Currently supports:

- **Soil Freeze Thaw (SFT)** - Retrieve paramters for Soil Freeze Thaw module
- **TopoFlow-Glacier** - Retrieve parameters for the TopoFlow Glacier module

### RAS Cross-sections
Retrieves geopackage data of HEC-RAS cross-sections

Currently supports:

- **HUC ID**: Download a geopackage for given HUC ID
- **HUC ID** and **Reach ID**: Download a geopackage for a given HUC ID and Reach ID

## Usage Examples

### Streamflow Observations

```python
import requests
import pandas as pd
from io import StringIO, BytesIO

base_url = "http://localhost:8000/v1/streamflow_observations"

# Get available data sources
sources = requests.get(f"{base_url}/sources").json()

# Get available identifiers for USGS
identifiers = requests.get(f"{base_url}/usgs/available", params={"limit": 10}).json()

# Get station information
station_info = requests.get(f"{base_url}/usgs/01031500/info").json()
print(f"Station has {station_info['total_records']} records")

# Download CSV data with date filtering
csv_response = requests.get(
    f"{base_url}/usgs/csv",
    params={
        "identifier": "01031500",
        "start_date": "2023-01-01T00:00:00",
        "end_date": "2023-01-31T00:00:00",
        "include_headers": True
    }
)
df_csv = pd.read_csv(StringIO(csv_response.text))

# Download Parquet data (recommended for large datasets)
parquet_response = requests.get(
    f"{base_url}/usgs/parquet",
    params={
        "identifier": "01031500",
        "start_date": "2023-01-01T00:00:00"
    }
)
df_parquet = pd.read_parquet(BytesIO(parquet_response.content))
```

### Hydrofabric Subset

```python
import requests

# Download hydrofabric subset as geopackage
response = requests.get("http://localhost:8000/v1/hydrofabric/01010000/gpkg")

if response.status_code == 200:
    with open("hydrofabric_subset_01010000.gpkg", "wb") as f:
        f.write(response.content)
    print(f"Downloaded {len(response.content)} bytes")
else:
    print(f"Error: {response.status_code}")
```

## Performance Considerations

### Data Format Recommendations

| Dataset Size | Recommended Format | Reason |
|-------------|-------------------|---------|
| < 50,000 records | CSV | Simple, widely supported |
| > 50,000 records | Parquet | Better compression, faster processing |
| > 200,000 records | Parquet + date filters | Reduced data transfer |

## Development

### Running the API

```bash
# Install dependencies
uv sync

# Start development server
python -m app.main
```

### Adding New Data Observation Sources

To add a new data source, update the configuration in your router:

Below is an example for the observations router

```python
class DataSource(str, Enum):
    USGS = "usgs"
    NEW_SOURCE = "new_source"  # Add new source

# Add configuration
DATA_SOURCE_CONFIG = {
    DataSource.NEW_SOURCE: {
        "namespace": "observations",
        "table": "new_source_table",
        "time_column": "timestamp",
        "units": "m³/s",
        "description": "New data source description",
    },
}
```

## API Documentation

### Interactive Documentation

The API provides interactive documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### OpenAPI Schema

Access the OpenAPI schema at: `http://localhost:8000/openapi.json`

## Verification

### Observations

```bash
# List available data sources
curl http://localhost:8000/v1/streamflow_observations/sources

# Get available identifiers (limit results)
curl "http://localhost:8000/v1/streamflow_observations/usgs/available?limit=5"

# Get data source information
curl http://localhost:8000/v1/streamflow_observations/usgs/info

# Get specific station information
curl http://localhost:8000/v1/streamflow_observations/usgs/01010000/info

# Download CSV with headers
curl "http://localhost:8000/v1/streamflow_observations/usgs/csv?identifier=01010000&include_headers=true"

# Download CSV with date filtering
curl "http://localhost:8000/v1/streamflow_observations/usgs/csv?identifier=01010000&start_date=2021-12-31T14%3A00%3A00&end_date=2022-01-01T14%3A00%3A00&include_headers=true"

# Download Parquet file
curl "http://localhost:8000/v1/streamflow_observations/usgs/parquet?identifier=01010000&start_date=2021-12-31T14%3A00%3A00&end_date=2022-01-01T14%3A00%3A00" -o "output.parquet"
```

### Hydrofabric

```bash
# Download hydrofabric subset
curl "http://localhost:8000/v1/hydrofabric/01010000/gpkg" -o "subset.gpkg"

# Download with different identifier
curl "http://localhost:8000/v1/hydrofabric/01031500/gpkg" -o "subset.gpkg"
```

### NWM Modules
```bash
# Return parameters for Soil Freeze Thaw by catchment
curl "http://localhost:8000/v1/modules/sft/?identifier=01010000&domain=conus_hf&use_schaake=false"

# Return albedo value for given catchment state (snow, ice, or other)
curl "http://localhost:8000/v1/modules/topoflow/albedo?landcover=snow"
```

### RAS Cross-sections
```bash
# Download RAS cross-sections for a HUC ID
curl "http://localhost:8000/v1/ras_xs/02040106/" -o "ras_02040106.gpkg"

# Download RAS cross-sections for a HUC ID and Reach ID
curl "http://localhost:8000/v1/ras_xs/02040106/dsreachid=4188251" -o "ras_02040106_4188251.gpkg"
```

### Health Check

```bash
# Check API health
curl http://localhost:8000/health
```
