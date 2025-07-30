import collections
import json
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
import polars as pl
import pyiceberg.exceptions as ex
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog, load_catalog
from pyproj import Transformer

from icefabric.hydrofabric import subset_hydrofabric
from icefabric.schemas.hydrofabric import HydrofabricDomains, IdType
from icefabric.schemas.modules import (
    LASAM,
    LSTM,
    SFT,
    SMP,
    CalibratableScheme,
    IceFractionScheme,
    NoahOwpModular,
    SacSma,
    SacSmaValues,
    Snow17,
    SoilScheme,
    Topmodel,
    Topoflow,
    TRoute,
)

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
    catalog = load_catalog("glue", **{"type": "glue", "glue.region": "us-east-1"})
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
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )
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


def get_snow17_parameters(
    catalog: Catalog, domain: HydrofabricDomains, identifier: str, conus_only: bool, envca: bool
) -> list[Snow17]:
    """Creates the initial parameter estimates for the Snow17 module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier
    conus_only : bool, optional
        If domain is CONUS, then set to True - otherwise False
    envca : bool, optional
        If source is ENVCA, then set to True - otherwise False.

    Returns
    -------
    list[Snow17]
        The list of all initial parameters for catchments using Snow17
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,

    )
    attr = {"elevation_mean": "mean.elevation", "lat": "centroid_y", "lon": "centroid_x"}

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Find all columns that start with the prefix
        matching_cols = [col for col in divide_attr_df.columns if col.startswith(prefix)]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    divide_attr_df = divide_attr_df.select(expressions)

    # Extraction of relevant features from divides layer
    divides_df = gauge["divides"][["divide_id", "areasqkm"]]

    # Ensure final result aligns properly based on each instances divide ids
    result_df = pd.merge(divide_attr_df.to_pandas(), divides_df, on="divide_id", how="left")

    # Convert elevation from cm to m
    result_df["elevation_mean"] = result_df["elevation_mean"] * 0.01

    # Convert CRS to WGS84 (EPSG4326)
    crs = gauge["divides"].crs
    transformer = Transformer.from_crs(crs, 4326)
    wgs84_latlon = transformer.transform(result_df["lon"], result_df["lat"])
    result_df["lon"] = wgs84_latlon[0]
    result_df["lat"] = wgs84_latlon[1]

    # Default parameter values used only for CONUS
    result_df["mfmax"] = CalibratableScheme.MFMAX
    result_df["mfmin"] = CalibratableScheme.MFMIN
    result_df["uadj"] = CalibratableScheme.UADJ

    if conus_only and not envca:
        divides_list = result_df["divide_id"]
        conus_param_df = divide_parameters(divides_list, "snow-17", HydrofabricDomains.CONUS.split("_")[0])
        result_df.drop(columns=["mfmax", "mfmin", "uadj"], inplace=True)
        result_df = pd.merge(conus_param_df, result_df, on="divide_id", how="left")

    pydantic_models = []
    for _idx, row_dict in result_df.iterrows():
        model_instance = Snow17(
            catchment=row_dict["divide_id"],
            hru_id=row_dict["divide_id"],
            hru_area=row_dict["areasqkm"],
            latitude=row_dict["lat"],
            elev=row_dict["elevation_mean"],
            mf_max=row_dict["mfmax"],
            mf_min=row_dict["mfmin"],
            uadj=row_dict["uadj"],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_smp_parameters(
    catalog: Catalog, domain: HydrofabricDomains, identifier: str, module: str = None
) -> list[SMP]:
    """Creates the initial parameter estimates for the SMP module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier
    module : str, optional
        A setting to determine if a module should be specified to obtain additional SMP parameters.
        Available modules declared for addt'l SMP parameters: 'CFE-S', 'CFE-X', 'LASAM', 'TopModel'

    Returns
    -------
    list[SMP]
        The list of all initial parameters for catchments using SMP
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,

    )
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

    # Initializing parameters dependent to unique modules
    soil_storage_model = "NA"
    soil_storage_depth = "NA"
    water_table_based_method = "NA"
    soil_moisture_profile_option = "NA"
    soil_depth_layers = "NA"
    water_depth_layers = "NA"
    water_table_depth = "NA"

    if module == "CFE-S" or module == "CFE-X":
        soil_storage_model = SoilScheme.CFE_SOIL_STORAGE.value
        soil_storage_depth = SoilScheme.CFE_STORAGE_DEPTH.value
    elif module == "TopModel":
        soil_storage_model = SoilScheme.TOPMODEL_SOIL_STORAGE.value
        water_table_based_method = SoilScheme.TOPMODEL_WATER_TABLE_METHOD.value
    elif module == "LASAM":
        soil_storage_model = SoilScheme.LASAM_SOIL_STORAGE.value
        soil_moisture_profile_option = SoilScheme.LASAM_SOIL_MOISTURE.value
        soil_depth_layers = SoilScheme.LASAM_SOIL_DEPTH_LAYERS.value
        water_table_depth = SoilScheme.LASAM_WATER_TABLE_DEPTH.value
    else:
        raise ValueError(f"Passing unsupported module into endpoint: {module}")

    pydantic_models = []
    for row_dict in result_df.iter_rows(named=True):
        # Instantiate the Pydantic model for each row
        model_instance = SMP(
            catchment=row_dict["divide_id"],
            smcmax=row_dict["smcmax_avg"],
            b=row_dict["bexp_avg"],
            satpsi=row_dict["psisat_avg"],
            soil_storage_model=soil_storage_model,
            soil_storage_depth=soil_storage_depth,
            water_table_based_method=water_table_based_method,
            soil_moisture_profile_option=soil_moisture_profile_option,
            soil_depth_layers=soil_depth_layers,
            water_depth_layers=water_depth_layers,
            water_table_depth=water_table_depth,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_lstm_parameters(catalog: Catalog, domain: HydrofabricDomains, identifier: str) -> list[LSTM]:
    """Creates the initial parameter estimates for the LSTM module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier

    Returns
    -------
    list[LSTM]
        The list of all initial parameters for catchments using LSTM

    *Note: Per HF API, the following attributes for LSTM does not carry any relvant information:
    'train_cfg_file' & basin_name' -- remove if desire
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,

    )
    attr = {
        "slope": "mean.slope",
        "elevation_mean": "mean.elevation",
        "lat": "centroid_y",
        "lon": "centroid_x",
    }

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Extract only the relevant attribute(s)
        matching_cols = [col for col in divide_attr_df.columns if col == prefix]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    divide_attr_df = divide_attr_df.select(expressions)

    # Extraction of relevant features from divides layer
    divides_df = gauge["divides"][["divide_id", "areasqkm"]]

    # Ensure final result aligns properly based on each instances divide ids
    result_df = pd.merge(divide_attr_df.to_pandas(), divides_df, on="divide_id", how="left")

    # Convert elevation from cm to m
    result_df["elevation_mean"] = result_df["elevation_mean"] * 0.01

    # Convert CRS to WGS84 (EPSG4326)
    crs = gauge["divides"].crs
    transformer = Transformer.from_crs(crs, 4326)
    wgs84_latlon = transformer.transform(result_df["lon"], result_df["lat"])
    result_df["lon"] = wgs84_latlon[0]
    result_df["lat"] = wgs84_latlon[1]

    pydantic_models = []
    for _idx, row_dict in result_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = LSTM(
            catchment=row_dict["divide_id"],
            area_sqkm=row_dict["areasqkm"],
            basin_id=identifier,
            elev_mean=row_dict["elevation_mean"],
            lat=row_dict["lat"],
            lon=row_dict["lon"],
            slope_mean=row_dict["slope"],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_lasam_parameters(
    catalog: Catalog,
    domain: HydrofabricDomains,
    identifier: str,
    sft_included: bool,
    soil_params_file: str = "vG_default_params_HYDRUS.dat",
) -> list[LASAM]:
    """Creates the initial parameter estimates for the LASAM module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier
    sft_included: bool
        True if SFT is in the "dep_modules_included" definition as declared in HF API repo.
    soil_params_file: str
        Name of the Van Genuchton soil parameters file. Note: This is the filename that gets returned by HF API's utility script
        get_hydrus_data().

    Returns
    -------
    list[LASAM]
        The list of all initial parameters for catchments using LASAM
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )
    attr = {"soil_type": "mode.ISLTYP"}

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Extract only the relevant attribute(s)
        matching_cols = [col for col in divide_attr_df.columns if col == prefix]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    result_df = divide_attr_df.select(expressions)

    pydantic_models = []
    for row_dict in result_df.iter_rows(named=True):
        # Instantiate the Pydantic model for each row
        model_instance = LASAM(
            catchment=row_dict["divide_id"],
            soil_params_file=soil_params_file,
            layer_soil_type=str(row_dict["soil_type"]),
            sft_coupled=sft_included,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_noahowp_parameters(
    catalog: Catalog, domain: HydrofabricDomains, identifier: str
) -> list[NoahOwpModular]:
    """Creates the initial parameter estimates for the Noah OWP Modular module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier

    Returns
    -------
    list[NoahOwpModular]
        The list of all initial parameters for catchments using NoahOwpModular
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )
    attr = {
        "slope": "mean.slope",
        "aspect": "circ_mean.aspect",
        "lat": "centroid_y",
        "lon": "centroid_x",
        "soil_type": "mode.ISLTYP",
        "veg_type": "mode.IVGTYP",
    }

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Extract only the relevant attribute(s)
        matching_cols = [col for col in divide_attr_df.columns if col == prefix]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    result_df = divide_attr_df.select(expressions).to_pandas()

    # Convert CRS to WGS84 (EPSG4326)
    crs = gauge["divides"].crs
    transformer = Transformer.from_crs(crs, 4326)
    wgs84_latlon = transformer.transform(result_df["lon"], result_df["lat"])
    result_df["lon"] = wgs84_latlon[0]
    result_df["lat"] = wgs84_latlon[1]

    pydantic_models = []
    for _idx, row_dict in result_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = NoahOwpModular(
            catchment=row_dict["divide_id"],
            lat=row_dict["lat"],
            lon=row_dict["lon"],
            terrain_slope=row_dict["slope"],
            azimuth=row_dict["aspect"],
            isltyp=row_dict["soil_type"],
            vegtyp=row_dict["veg_type"],
            sfctyp=2 if row_dict["veg_type"] == 16 else 1,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_sacsma_parameters(
    catalog: Catalog, domain: HydrofabricDomains, identifier: str, conus_only: bool, envca: bool
) -> list[SacSma]:
    """Creates the initial parameter estimates for the SAC SMA module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier
    conus_only : bool, optional
        If domain is CONUS, then set to True
    envca : bool, optional
        If source is ENVCA, then set to True - otherwise False.

    Returns
    -------
    list[SacSma]
        The list of all initial parameters for catchments using SacSma
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )

    # Extraction of relevant features from divides layer
    pd.options.mode.chained_assignment = None
    result_df = gauge["divides"][["divide_id", "areasqkm"]]

    # Default parameter values used only for CONUS
    result_df["uztwm"] = SacSmaValues.UZTWM.value
    result_df["uzfwm"] = SacSmaValues.UZFWM.value
    result_df["lztwm"] = SacSmaValues.LZTWM.value
    result_df["lzfpm"] = SacSmaValues.LZFPM.value
    result_df["lzfsm"] = SacSmaValues.LZFSM.value
    result_df["adimp"] = SacSmaValues.ADIMP.value
    result_df["uzk"] = SacSmaValues.UZK.value
    result_df["lzpk"] = SacSmaValues.LZPK.value
    result_df["lzsk"] = SacSmaValues.LZSK.value
    result_df["zperc"] = SacSmaValues.ZPERC.value
    result_df["rexp"] = SacSmaValues.REXP.value
    result_df["pctim"] = SacSmaValues.PCTIM.value
    result_df["pfree"] = SacSmaValues.PFREE.value
    result_df["riva"] = SacSmaValues.RIVA.value
    result_df["side"] = SacSmaValues.SIDE.value
    result_df["rserv"] = SacSmaValues.RSERV.value

    if conus_only and not envca:
        divides_list = result_df["divide_id"]
        conus_param_df = divide_parameters(divides_list, "sac-sma", HydrofabricDomains.CONUS.split("_")[0])
        result_df.drop(
            columns=[
                "uztwm",
                "uzfwm",
                "lztwm",
                "lzfpm",
                "lzfsm",
                "uzk",
                "lzpk",
                "lzsk",
                "zperc",
                "rexp",
                "pfree",
            ],
            inplace=True,
        )
        result_df = pd.merge(conus_param_df, result_df, on="divide_id", how="left")

    pydantic_models = []
    for _idx, row_dict in result_df.iterrows():
        # Instantiate the Pydantic model for each row
        # *Note: The HF API declares hru_id as the divide id, but to remain consistent
        # keeping catchment arg.
        model_instance = SacSma(
            catchment=row_dict["divide_id"],
            hru_id=row_dict["divide_id"],
            hru_area=row_dict["areasqkm"],
            uztwm=row_dict["uztwm"],
            uzfwm=row_dict["uzfwm"],
            lztwm=row_dict["lztwm"],
            lzfpm=row_dict["lzfpm"],
            lzfsm=row_dict["lzfsm"],
            uzk=row_dict["uzk"],
            lzpk=row_dict["lzpk"],
            lzsk=row_dict["lzsk"],
            zperc=row_dict["zperc"],
            rexp=row_dict["rexp"],
            pfree=row_dict["pfree"],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_troute_parameters(catalog: Catalog, domain: HydrofabricDomains, identifier: str) -> list[TRoute]:
    """Creates the initial parameter estimates for the T-Route

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier

    Returns
    -------
    list[TRoute]
        The list of all initial parameters for catchments using TRoute
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )

    # Extraction of relevant features from divide attributes layer
    divide_attr_df = pd.DataFrame(gauge["divide-attributes"])
    nwtopo_param = collections.defaultdict(dict)
    nwtopo_param["supernetwork_parameters"].update({"geo_file_path": f"gauge_{identifier}.gpkg"})
    nwtopo_param["waterbody_parameters"].update(
        {"level_pool": {"level_pool_waterbody_parameter_file_path": f"gauge_{identifier}.gpkg"}}
    )

    pydantic_models = []
    for _idx, row_dict in divide_attr_df.iterrows():
        model_instance = TRoute(catchment=row_dict["divide_id"], nwtopo_param=nwtopo_param)
        pydantic_models.append(model_instance)
    return pydantic_models


def get_topmodel_parameters(catalog: Catalog, domain: HydrofabricDomains, identifier: str) -> list[Topmodel]:
    """Creates the initial parameter estimates for the Topmodel

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier

    Returns
    -------
    list[Topmodel]
        The list of all initial parameters for catchments using Topmodel

    *Note:

    - Per HF API SME, relevant information presented here will only source info that was
    written to the HF API's {divide_id}_topmodel_subcat.dat & {divide_id}_topmodel_params.dat
    files.

    - The divide_id is the same as catchment, but will return divide_id variable name here
    since expected from HF API - remove if needed.
    """
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain.value}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=f"gages-{identifier}",
        id_type=IdType.HL_URI,
        namespace=domain.value,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        upstream_dict=upstream_dict,
    )
    attr = {"twi": "dist_4.twi"}

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Extract only the relevant attribute(s)
        matching_cols = [col for col in divide_attr_df.columns if col == prefix]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    divide_attr_df = divide_attr_df.select(expressions)

    # Extraction of relevant features from divides layer
    divides_df = gauge["divides"][["divide_id", "lengthkm"]]

    # Ensure final result aligns properly based on each instances divide ids
    result_df = pd.merge(divide_attr_df.to_pandas(), divides_df, on="divide_id", how="left")

    pydantic_models = []
    for _idx, row_dict in result_df.iterrows():
        twi_json = json.loads(row_dict["twi"])
        model_instance = Topmodel(
            catchment=row_dict["divide_id"],
            divide_id=row_dict["divide_id"],
            twi=twi_json,
            num_topodex_values=len(twi_json),
            dist_from_outlet=round(row_dict["lengthkm"] * 1000),
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_topoflow_parameters(catalog: Catalog, domain: HydrofabricDomains, identifier: str) -> list[Topoflow]:
    """Creates the initial parameter estimates for the Topoflow module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    domain : HydrofabricDomains
        the hydrofabric domain
    identifier : str
        the gauge identifier

    Returns
    -------
    list[Topoflow]
        The list of all initial parameters for catchments using Topoflow

    *Note: This is a placeholder for Topoflow as the generation of IPEs for
    Topoflow does not exist currently.
    """
    raise NotImplementedError("Topoflow not implemented yet")
