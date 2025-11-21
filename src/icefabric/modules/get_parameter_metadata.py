import numpy as np
from pyiceberg.catalog import Catalog


def get_parameter_metadata(module: str, catalog: Catalog, calibratable: bool = True, metadata: list = None):
    """Returns parameter metadata from a module

    Parameters
    ----------
    module: str
        the module name
    catalog : Catalog
        the pyiceberg lakehouse catalog
    calibratable : bool
        return only calibratable parameter if true, otherwise return all parameters.
        Defaults to true
    metadata : list
        a list of columns to return. If not included, name, description, units, data_type,
        default_value, min, max are returned

    Returns
    -------
    dict
        A dictionary containting the module name and parameter metadata
    """
    # if metadata argument is empty, set default columns to return
    if metadata is None:
        metadata = ["name", "description", "units", "data_type", "default_value", "min", "max"]
    # make sure that the name gets returned when the user selects the columns to return
    elif "name" not in metadata:
        metadata.insert(0, "name")

    # Read table from Iceberg to Pandas and replace any NaNs with None to support JSON output
    namespace = "parameter_metadata"
    table_name = "parameter_metadata"
    table = catalog.load_table(f"{namespace}.{table_name}")
    df = table.scan().to_pandas()
    df = df.replace(np.nan, None)

    # Separate query strings to support CFE-S and CFE-X
    if module == "cfe-x":
        query_string = "(module == 'cfe-x' or module == 'cfe') and calibratable == @calibratable"
    elif module == "cfe-s":
        query_string = "module == 'cfe' and calibratable == @calibratable"
    else:
        query_string = "module == @module and calibratable == @calibratable"

    module_params = df.query(query_string)[metadata]
    # convert dataframe to a list of dictionaries
    module_params_dict = module_params.to_dict(orient="records")
    # create dictionary with module name and list of calibratable parameters
    output = {"module_name": module, "calibratable_parameters": module_params_dict}

    return output
