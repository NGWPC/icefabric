from functools import reduce

import numpy as np
import pandas as pd
import rustworkx as rx
from pyiceberg.catalog import Catalog

from icefabric.modules.create_ipes import get_subset
from icefabric.modules.divide_attributes import (
    ParametersToDivideAttributesHF,
    ParametersToDivideAttributesNHF,
)
from icefabric.schemas.hydrofabric import HydrofabricNamespace


def get_parameter_metadata(
    modules: list[str],
    catalog: Catalog,
    calibratable: bool = True,
    metadata: list = None,
    gage_id: str = None,
    domain: HydrofabricNamespace | None = None,
    graph: rx.PyDiGraph = None,
):
    """Returns parameter metadata from a module

    Parameters
    ----------
    modules: list[str]
        the module names to get parameter metadata for
    catalog : Catalog
        the pyiceberg lakehouse catalog
    calibratable : bool
        return only calibratable parameter if true, otherwise return all parameters.
        Defaults to true
    metadata : list
        a list of columns to return. If not included, name, description, units, data_type,
        initial_value, min, max are returned
    gage_id: str
        if provided, the subsetter is run for the gage and basin averaged parameters are returned for initial value

    Returns
    -------
    dict
        A dictionary containting the module name and parameter metadata
    """
    # if metadata argument is empty, set default columns to return
    if metadata is None:
        metadata = ["name", "description", "units", "data_type", "initial_value", "min", "max"]

    # make sure that the name gets returned when the user selects the columns to return
    if "name" not in metadata:
        metadata.insert(0, "name")

    # Read table from Iceberg to Pandas and replace any NaNs with None to support JSON output
    namespace = "parameter_metadata"
    table_name = "parameter_metadata"
    table = catalog.load_table(f"{namespace}.{table_name}")
    df = table.scan().to_pandas()
    df = df.replace(np.nan, None)

    if gage_id is not None:
        gauge = get_subset(catalog=catalog, identifier=gage_id, namespace=domain, graph=graph)

        # If 2.2, get snow17, sac-sma, and cfe-x attributes from iceberg tables and divide area from
        # the divides layer.  Merge into a single dataframe for area weighted averaging.
        if not domain.is_nhf:
            parameter_namespace = "divide_parameters"
            snow17_table = "snow-17_conus"
            sacsma_table = "sac-sma_conus"
            cfex_table = "cfe-x_conus"

            divide_attrs = pd.DataFrame(gauge["divide-attributes"])
            area = pd.DataFrame(gauge["divides"])[["divide_id", "areasqkm"]]

            table = catalog.load_table(f"{parameter_namespace}.{snow17_table}")
            snow17 = table.scan().to_pandas()

            table = catalog.load_table(f"{parameter_namespace}.{sacsma_table}")
            sacsma = table.scan().to_pandas()

            table = catalog.load_table(f"{parameter_namespace}.{cfex_table}")
            cfex = table.scan().to_pandas()

            divide_attrs = reduce(
                lambda left, right: pd.merge(left, right, on="divide_id", how="inner"),
                [divide_attrs, snow17, sacsma, cfex, area],
            )
            divide_attrs = divide_attrs.rename(columns={"areasqkm": "area_sqkm"})
        else:
            divide_attrs = pd.DataFrame(gauge["divides"])

    output_list = []

    for module in modules:
        # Separate query strings to support CFE-S and CFE-X
        if module == "cfe-x":
            query_string = "(module == 'cfe-x' or module == 'cfe') and calibratable == @calibratable"
            check_module_name = "cfe"
        elif module == "cfe-s":
            query_string = "module == 'cfe' and calibratable == @calibratable"
            check_module_name = "cfe"
        else:
            query_string = "module == @module and calibratable == @calibratable"
            check_module_name = module

        # Modules that are valid but don't have parameter metadata yet
        modules_without_metadata = {"troute", "lstm", "pet"}

        if check_module_name in modules_without_metadata:
            output = {"module_name": module, "calibratable_parameters": []}
            output_list.append(output)
            continue

        if df["module"].isin([check_module_name]).any():
            module_params = df.query(query_string)[metadata]

            # For each parameter, check if the name maps to an NHF or 2.2 divide attribute name,
            # then compute a basin area weighted average.  If the divide attributes do not exist for the gage,
            # return the original initial value.
            if gage_id is not None:
                parameter_lookup = (
                    ParametersToDivideAttributesNHF.parametersNHF
                    if domain.is_nhf
                    else ParametersToDivideAttributesHF.parametersHF
                )
                for index, row in module_params.iterrows():
                    param_name = row["name"]
                    if param_name in parameter_lookup.keys():
                        attr_name = parameter_lookup[param_name]
                        if attr_name in divide_attrs.columns:
                            attr = divide_attrs[[attr_name, "area_sqkm"]]
                            attr = attr[attr[attr_name].notna()]
                            if len(attr) == 0:
                                continue
                            numerator = (attr[attr_name] * attr["area_sqkm"]).sum()
                            denominator = attr["area_sqkm"].sum()
                            weighted_avg = numerator / denominator if denominator != 0 else None
                            module_params.at[index, "initial_value"] = weighted_avg

            # convert dataframe to a list of dictionaries
            module_params_dict = module_params.to_dict(orient="records")
            # create dictionary with module name and list of calibratablie parameters
            output = {"module_name": module, "calibratable_parameters": module_params_dict}
        else:
            output = {"module_name": module, "error": "Not a valid module name"}

        output_list.append(output)

    return output_list
