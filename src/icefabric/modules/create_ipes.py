import os

import geopandas as gpd
import pandas as pd
import polars as pl
import pyiceberg.exceptions as ex
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog, load_catalog

from icefabric.hydrofabric import subset
from icefabric.schemas.hydrofabric import HydrofabricDomains, IdType
from icefabric.schemas.modules import SFT, IceFractionScheme

ROOT_DIR = os.path.abspath(os.curdir)


def _get_mean_soil_temp() -> float:
    """Returns an avg soil temp of 45 degrees F converted to Kelvin. This equation is just a reasonable estimate per new direction (EW: 07/2025)

    Returns
    -------
    float
        The mean soil temperature
    """
    return (45 - 32) * 5 / 9 + 273.15


def divide_parameters(divides, module, domain):
    """Returns iceberg divide parameters"""
    module = module.lower()
    domain = domain.lower()
    namespace = "divide_parameters"
    table_name = f"{namespace}.{module}_{domain}"
    catalog = load_catalog("glue")
    try:
        table = catalog.load_table(table_name)
    except ex.NoSuchTableError:
        print(f"Table {table_name} does not exist")
        return pd.DataFrame()
    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 endpoint"
        print(msg)
        raise e
    df = table.scan().to_pandas()
    filtered = df[df["divide_id"].isin(divides)]
    return filtered


def get_sft_parameters(
    catalog: Catalog, domain: HydrofabricDomains, identifier: str, use_schaake: bool = False
) -> list[SFT]:
    """Creates the initial parameter estimates for the SFT module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier
    use_schaake : bool, optional
        A setting to determine if Shaake should be used for ice fraction, by default False

    Returns
    -------
    list[SFT]
        The list of all initial parameters for catchments using SFT
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        domain=domain,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
    )  # type: ignore
    attr = {"smcmax": "mean.smcmax", "bexp": "mode.bexp", "psisat": "geom_mean.psisat"}

    df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]  # Keep the divide_id
    for param_name, prefix in attr.items():
        # Find all columns that start with the prefix
        matching_cols = [col for col in df.columns if col.startswith(prefix)]
        if matching_cols:
            # Calculate mean across matching columns for each row.
            # NOTE: this assumes an even weighting. TODO: determine if we need to have weighted averaging
            expressions.append(
                pl.concat_list([pl.col(col) for col in matching_cols]).list.mean().alias(f"{param_name}_avg")
            )
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}_avg"))
    result_df = df.select(expressions)
    mean_temp = _get_mean_soil_temp()
    pydantic_models = []
    for row_dict in result_df.iter_rows(named=True):
        # Instantiate the Pydantic model for each row
        model_instance = SFT(
            catchment=row_dict["divide_id"],
            smcmax=row_dict["smcmax_avg"],
            b=row_dict["bexp_avg"],
            satpsi=row_dict["psisat_avg"],
            ice_fraction_scheme=IceFractionScheme.XINANJIANG
            if use_schaake is False
            else IceFractionScheme.SCHAAKE,
            soil_temperature=[
                mean_temp for _ in range(4)
            ],  # Assuming 45 degrees in all layers. TODO: Fix this as this doesn't make sense
        )
        pydantic_models.append(model_instance)
    return pydantic_models
