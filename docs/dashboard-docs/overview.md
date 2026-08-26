# Dashboard Overview

The Icefabric Dashboard is a Streamlit-based web application that makes it easy for users to visualize and explore the hydrologic datasets within the Icefabric umbrella.

## Key Features

- **Explore hydrologic datasets:**
  Browse NGWPC Hydrofabric network components (flowpaths, nexuses, divides, waterbodies, and more), as well as RAS XS (HEC-RAS Cross-Sectional) data.

- **Subset the Hydrofabric:**
  Provide a flowpath ID or USGS gage ID and let the dashboard trace upstream automatically.

- **Visualize geospatial data:**
  View subsets on interactive Leaflet maps. Draw bounding boxes to explore the RAS XS data in specific user-defined locations.

- **Interact with streamflow records:**
  Access USGS streamflow time series and zoomable hydrographs.

- **Download data:**
  Export subsets as GeoPackage files.

- **Supports multiple catalogs:**
  Choose between:
    - AWS Glue Iceberg catalog
    - Local SQLite Iceberg catalog for offline work

## System Components

Although the dashboard is part of the Icefabric project, it runs independently:

- It reads directly from the Iceberg catalog (Glue or SQLite) and the S3 Icechunk store.
- It does **not** require the Icefabric API to be running.
