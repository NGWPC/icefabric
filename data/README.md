# Icefabric Data Directory

This directory is meant to both store smaller csv files (<50MB) to allow for data access through Github, as well as scripts to create larger data objects that are used by API/CLIs

### Hydrofabric Upstream Connections
To speed up processing of hydrofabric subsetting, upstream connections have been preprocessed into JSON files in order to determine upstream flow connectivitity. In this case, the `key` of the JSON object is the downstream flowpath and the `values` are the upstream flowpaths. Also, in this file, there is metadata to provide the data, and HF snapshot used to create these files.

### Module iniial parameters
CSV files for initial parameterizations are kept in the `modules_ipes` folder for versioning of default parameters.

### Scripts to create data files:
*Hydrofabric Upstream Connections*
```sh
icefabric build-upstream-connections --help
Usage: icefabric build-upstream-connections [OPTIONS]

  Creates a JSON file which documents the upstream connections from a
  particular basin

Options:
  --catalog [glue|sql]            The pyiceberg catalog type
  --domain [ak_hf|conus_hf|gl_hf|hi_hf|prvi_hf]
                                  The domain you are querying  [required]
  -o, --output-path PATH          Output path of the upstream connections json
  --help                          Show this message and exit.
```
