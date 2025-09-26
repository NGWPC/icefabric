# Icefabric API Guide

## Overview

The Icefabric API is a FastAPI-based service that provides access to EDFS data stored in both Apache Iceberg & Icechunk format. The API offers multiple data export formats and metadata endpoints for the hydrofabric and streamflow observations.

## Architecture

The API consists of several key components:

1. **Main Application** (`app/main.py`) - FastAPI application with health checks and router configuration
2. **Data Routers** - Handles all data endpoints. Streamflow observations, Hydrofabric subsetting, National Water Model module configuration, and HEC-RAS cross-section retrieval are supported.
   - **RISE Wrapper API** - Also has a wrapper API to the RISE API from the Bureau of Reclamation
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
2. **Data Filtering** - Applies optional date range filters to Icechunk datasets
3. **Format Conversion** - Exports data in requested format (CSV/Parquet)
4. **Response Generation** - Returns data with appropriate headers and metadata

### Supported Data Sources

#### Observations
Download hourly data from (and get info on) the Icechunk streamflow repository. Currently has data from the following sources:

- **USGS** - 'United States Geological Survey' hourly streamflow data
- **ENVCA** - 'Environmental California' hourly streamflow data
- **CADWR** - 'California Department of Water Resources' hourly streamflow data
- **TXDOT** - 'Texas Department of Transportation' hourly streamflow data

#### Hydrofabric
Provides geospatial watershed data:

- **Subset Generation** - Creates upstream watershed subsets from identifiers
- **History** - Gets the iceberg snapshot history for a specific domain namespace

!!! note "Data Storage"
    All data is stored remotely as Apache Iceberg tables on AWS glue unless you built the catalog locally. Then, it is stored at SQLite-backed catalog locally built at `/tmp/warehouse/pyiceberg_catalog.db`

### National Water Model Modules
Retrieve National Water Model (NWM) module parameters.

Currently supports:

- **SFT (Soil Freeze-Thaw)** - Retrieve parameters for the Soil Freeze-Thaw module
- **SNOW-17 (Snow Accumulation and Ablation Model)** - Retrieve parameters for the Snow Accumulation and Ablation Model module
- **SMP (Soil Moisture Profile)** - Retrieve parameters for the Soil Moisture Profile module
- **LSTM (Long Short-Term Memory)** - Retrieve parameters for the Long Short-Term Memory module
- **LASAM (Lumped Arid/Semi-arid Model)** - Retrieve parameters for the Lumped Arid/Semi-arid Model module
- **Noah-OWP-Modular** - Retrieve parameters for the Noah-OWP-Modular module
- **SAC-SMA (Sacramento Soil Moisture Accounting)** - Retrieve parameters for the Sacramento Soil Moisture Accounting module
- **T-Route (Tree-Based Channel Routing)** - Retrieve parameters for the Tree-Based Channel Routing module
- **TOPMODEL** - Retrieve parameters for the TOPMODEL module

#### Other

- **TopoFlow-Glacier Albedo** - Return TopoFlow-Glacier albedo value for given catchment state (snow, ice, or other)

### RAS Cross-sections
Retrieves geopackage data of HEC-RAS cross-sections. The cross-sectional data is in two schemas:
- **Conflated**: HEC-RAS data mapped to nearest reference hydrofabric flowpath. Many per flowpath ID.
- **Representative**: The median, representative, cross-sections - derived from the conflated data set. As such, there is one per reference hydrofabric flowpath ID.

Currently supports the following query types (both can retrieve data from either conflated or representative datasets):
- **Flowpath ID**: Download a geopackage for given flowpath ID.
- **Geospatial Query**: Download a geopackage that contains every instance of XS line-data inside a provided lat/lon bounding box.

## Usage Examples

### Streamflow Observations

```python
import requests
import pandas as pd
from io import StringIO, BytesIO

base_url = "http://localhost:8000/v1/streamflow_observations"

# Get available identifiers
identifiers = requests.get(f"{base_url}/available", params={"limit": 10}).json()

# Get station information
station_info = requests.get(f"{base_url}/01031500/info").json()
print(f"Station has {station_info['total_records']} records")

# Download CSV data with date filtering
csv_response = requests.get(
    f"{base_url}/01031500/csv",
    params={
        "start_date": "2023-01-01 00:00:00",
        "end_date": "2023-01-31 00:00:00",
        "include_headers": True
    }
)
df_csv = pd.read_csv(StringIO(csv_response.text))

# Download Parquet data (recommended for large datasets)
parquet_response = requests.get(
    f"{base_url}/01031500/parquet",
    params={
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

### RAS-XS

```python
import geopandas as gpd
import httpx

from icefabric.schemas import XsType
from pyiceberg.expressions import In

# Set up parameters for the API call
flowpath_id = "20059822"
url = f"http://0.0.0.0:8000/v1/ras_xs/{flowpath_id}/"
schema_type = XsType.CONFLATED
params = {
    "schema_type": schema_type.value,
}
headers = {"Content-Type": "application/json"}

# Use HTTPX to stream the resulting geopackage response
with (
    httpx.stream(
        method="GET",
        url=url,
        params=params,
        headers=headers,
        timeout=60.0,  # GLUE API requests can be slow depending on the network speed. Adding a 60s timeout to ensure requests go through
    ) as response
):
    response.raise_for_status()  # Ensure the request was successful
    with open(f"ras_xs_{flowpath_id}.gpkg", "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)

# Load geopackage into geopandas
gdf = gpd.read_file(f"ras_xs_{flowpath_id}.gpkg")

# Pull and filter reference divides/flowpaths from the catalog
reference_divides = to_geopandas(
    catalog.load_table("conus_reference.reference_divides")
    .scan(row_filter=In("flowpath_id", gdf["flowpath_id"]))
    .to_pandas()
)
reference_flowpaths = to_geopandas(
    catalog.load_table("conus_reference.reference_flowpaths")
    .scan(row_filter=In("flowpath_id", gdf["flowpath_id"]))
    .to_pandas()
)

# Convert all data to the EPSG:4326 coordinate reference system
reference_divides = reference_divides.to_crs(epsg=4326)
reference_flowpaths = reference_flowpaths.to_crs(epsg=4326)
gdf = gdf.to_crs(epsg=4326)

ref_div_ex = reference_divides.explore(color="grey")
ref_flo_ex = reference_flowpaths.explore(m=ref_div_ex, color="blue")

# View the data
gdf.explore(m=ref_flo_ex, color="black")
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

## API Documentation

### Interactive Documentation

The API provides interactive documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### OpenAPI Schema

Access the OpenAPI schema at: `http://localhost:8000/openapi.json`

## Verification

### Hourly Streamflow Observations

Interface for querying the hourly streamflow dataset. Includes USGS/ENVCA/CADWR/TXDOT gages. Can return data as CSV or Parquet files in specified date ranges.

#### Endpoint Examples
```bash
# Get available identifiers (limit results)
curl "http://localhost:8000/v1/streamflow_observations/available?limit=5"

# Get dataset repo history (snapshots, commit messages, etc.)
curl "http://localhost:8000/v1/streamflow_observations/history"

# Get specific station information
curl "http://localhost:8000/v1/streamflow_observations/JBR/info"

# Download gage data (full set) CSV with headers
curl "http://localhost:8000/v1/streamflow_observations/01031500/csv?include_headers=true"

# Download CSV with date filtering - 2010 to 2011
curl "http://localhost:8000/v1/streamflow_observations/02GC002/csv?start_date=2010&end_date=2011"

# Download Parquet file with date filtering - June 2023 to November 2023
curl "http://localhost:8000/v1/streamflow_observations/08102730/parquet?start_date=2023-06&end_date=2023-11"
```

### Hydrofabric

Interface for querying the Hydrofabric service.

#### Endpoint Examples
```bash
# Download hydrofabric subset
curl "http://localhost:8000/v1/hydrofabric/01010000/gpkg" -o "subset.gpkg"

# Download with different identifier
curl "http://localhost:8000/v1/hydrofabric/01031500/gpkg" -o "subset.gpkg"
```

```bash
# Get iceberg snapshot history for the CONUS domain
curl "http://localhost:8000/v1/hydrofabric/history?domain=conus_hf
```

### NWM Modules

Interface for NWM modules. Each module supports IPE return, given a gage ID and module-appropriate extra information.

#### Endpoint Examples
```bash
# Return parameters for SFT (Soil Freeze-Thaw) by catchment
curl "http://localhost:8000/v1/modules/sft/?identifier=01010000&domain=conus_hf&use_schaake=false"

# Return parameters for SNOW-17 (Snow Accumulation and Ablation Model) by catchment
curl "http://localhost:8000/v1/modules/snow17/?identifier=01010000&domain=conus_hf&envca=false"

# Return parameters for SMP (Soil Moisture Profile) by catchment
curl "http://localhost:8000/v1/modules/smp/?identifier=01010000&domain=conus_hf&module=CFE-S"

# Return parameters for LSTM (Long Short-Term Memory) by catchment
curl "http://localhost:8000/v1/modules/lstm/?identifier=01010000&domain=conus_hf"

# Return parameters for LASAM (Lumped Arid/Semi-arid Model) by catchment
curl "http://localhost:8000/v1/modules/lasam/?identifier=01010000&domain=conus_hf&sft_included=false&soil_params_file=vG_default_params_HYDRUS.dat"

# Return parameters for Noah-OWP-Modular by catchment
curl "http://localhost:8000/v1/modules/noahowp/?identifier=01010000&domain=conus_hf"

# Return parameters for SAC-SMA (Sacramento Soil Moisture Accounting) by catchment
curl "http://localhost:8000/v1/modules/sacsma/?identifier=01010000&domain=conus_hf&envca=false"

# Return parameters for T-Route (Tree-Based Channel Routing) by catchment
curl "http://localhost:8000/v1/modules/troute/?identifier=01010000&domain=conus_hf"

# Return parameters for TOPMODEL by catchment
curl "http://localhost:8000/v1/modules/topmodel/?identifier=01010000&domain=conus_hf"

# Return albedo value for given catchment state (snow, ice, or other)
curl "http://localhost:8000/v1/modules/topoflow/albedo?landcover=snow"
```

### RAS Cross-sections

Interface for querying HEC-RAS cross-sectional data. Supports per-flowpath-ID queries and lat/lon bounding box queries.
Each flowpath is composed of conflated cross-sections. Each flowpath has one 'averaged' representative cross-section.

#### Endpoint Examples
```bash
# Download conflated RAS cross-sections for a flowpath ID
curl "http://localhost:8000/v1/ras_xs/20059822/?schema_type=conflated"

# Download representative RAS cross-sections for a flowpath ID
curl "http://localhost:8000/v1/ras_xs/20059822/?schema_type=representative"

# Download RAS cross-sections that lie within a geospatial lat/lon bounding box
# NOTE - can also get representative cross-sections when querying by bounding-box
curl "http://localhost:8000/v1/ras_xs/within?schema_type=conflated&min_lat=31.3323&min_lon=-109.0502&max_lat=37.0002&max_lon=-103.002"
```

### RISE API Wrapper

A wrapper interface to the [RISE API](https://data.usbr.gov/rise-api). Used to query reservoir outflow data.

#### Endpoint Examples
```bash
# Get the collection of 'CatalogItem' resources - customize response by setting page quantity and items per page.
curl "http://localhost:8000/v1/rise/catalog-item?page=1&itemsPerPage=25"

# Get a 'CatalogItem' resource, per a given ID.
curl "http://localhost:8000/v1/rise/catalog-item/10833"

# Get the collection of 'CatalogRecord' resources - customize response by setting page quantity and items per page.
curl "http://localhost:8000/v1/rise/catalog-record?page=1&itemsPerPage=25"

# Get a 'CatalogRecord' resource, per a given ID.
curl "http://localhost:8000/v1/rise/catalog-record/8134"

# Get the collection of 'Location' resources - customize response by setting page quantity and items per page.
curl "http://localhost:8000/v1/rise/location?page=1&itemsPerPage=25"

# Get a 'Location' resource, per a given ID.
curl "http://localhost:8000/v1/rise/location/3708"

# Get a 'Result' resource, per a given ID.
curl "http://localhost:8000/v1/rise/result/8000"
```

### Health Check

```bash
# Check API health
curl http://localhost:8000/health
```
