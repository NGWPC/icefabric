import collections
import json

import geopandas as gpd
import pandas as pd
import polars as pl
import rustworkx as rx
from ambiance import Atmosphere
from pyiceberg.catalog import Catalog
from pyproj import Transformer

from icefabric.hydrofabric import subset_hydrofabric
from icefabric.schemas.hydrofabric import IdType
from icefabric.schemas.modules import (
    CFE,
    LASAM,
    LSTM,
    SFT,
    SMP,
    UEB,
    CalibratableScheme,
    CFEValues,
    IceFractionScheme,
    NoahOwpModular,
    SacSma,
    SacSmaValues,
    Snow17,
    SoilScheme,
    Topmodel,
    Topoflow,
    TRoute,
    UEBValues,
)


def _get_mean_soil_temp() -> float:
    """Returns an avg soil temp of 45 degrees F converted to Kelvin. This equation is just a reasonable estimate per new direction (EW: 07/2025)

    Returns
    -------
    float
        The mean soil temperature
    """
    return (45 - 32) * 5 / 9 + 273.15


def get_sft_parameters(
    catalog: Catalog,
    namespace: str,
    identifier: str,
    graph: rx.PyDiGraph,
    use_schaake: bool = False,
) -> list[SFT]:
    """Creates the initial parameter estimates for the SFT module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    use_schaake : bool, optional
        A setting to determine if Shaake should be used for ice fraction, by default False

    Returns
    -------
    list[SFT]
        The list of all initial parameters for catchments using SFT
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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
    catalog: Catalog, namespace: str, identifier: str, envca: bool, graph: rx.PyDiGraph
) -> list[Snow17]:
    """Creates the initial parameter estimates for the Snow17 module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    envca : bool, optional
        If source is ENVCA, then set to True - otherwise False.

    Returns
    -------
    list[Snow17]
        The list of all initial parameters for catchments using Snow17
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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
    result_df["mfmax"] = CalibratableScheme.MFMAX.value
    result_df["mfmin"] = CalibratableScheme.MFMIN.value
    result_df["uadj"] = CalibratableScheme.UADJ.value

    if namespace == "conus_hf" and not envca:
        divides_list = result_df["divide_id"]
        domain = namespace.split("_")[0]
        table_name = f"divide_parameters.snow-17_{domain}"
        params_df = catalog.load_table(table_name).to_polars()
        conus_param_df = params_df.filter(pl.col("divide_id").is_in(divides_list)).collect().to_pandas()
        result_df.drop(columns=["mfmax", "mfmin", "uadj"], inplace=True)
        result_df = pd.merge(conus_param_df, result_df, on="divide_id", how="left")

    pydantic_models = []
    for _, row_dict in result_df.iterrows():
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
    catalog: Catalog,
    namespace: str,
    identifier: str,
    graph: rx.PyDiGraph,
    extra_module: str | None = None,
) -> list[SMP]:
    """Creates the initial parameter estimates for the SMP module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    extra_module : str, optional
        A setting to determine if a module should be specified to obtain additional SMP parameters.
        Available modules declared for addt'l SMP parameters: 'CFE-S', 'CFE-X', 'LASAM', 'TopModel'

    Returns
    -------
    list[SMP]
        The list of all initial parameters for catchments using SMP
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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

    if extra_module:
        if extra_module == "CFE-S" or extra_module == "CFE-X":
            soil_storage_model = SoilScheme.CFE_SOIL_STORAGE.value
            soil_storage_depth = SoilScheme.CFE_STORAGE_DEPTH.value
        elif extra_module == "TopModel":
            soil_storage_model = SoilScheme.TOPMODEL_SOIL_STORAGE.value
            water_table_based_method = SoilScheme.TOPMODEL_WATER_TABLE_METHOD.value
        elif extra_module == "LASAM":
            soil_storage_model = SoilScheme.LASAM_SOIL_STORAGE.value
            soil_moisture_profile_option = SoilScheme.LASAM_SOIL_MOISTURE.value
            soil_depth_layers = SoilScheme.LASAM_SOIL_DEPTH_LAYERS.value
            water_table_depth = SoilScheme.LASAM_WATER_TABLE_DEPTH.value
        else:
            raise ValueError(f"Passing unsupported module into endpoint: {extra_module}")

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


def get_lstm_parameters(catalog: Catalog, namespace: str, identifier: str, graph: rx.PyDiGraph) -> list[LSTM]:
    """Creates the initial parameter estimates for the LSTM module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier

    Returns
    -------
    list[LSTM]
        The list of all initial parameters for catchments using LSTM

    *Note: Per HF API, the following attributes for LSTM does not carry any relvant information:
    'train_cfg_file' & basin_name' -- remove if desire
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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
    for _, row_dict in result_df.iterrows():
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
    namespace: str,
    identifier: str,
    sft_included: bool,
    graph: rx.PyDiGraph,
    soil_params_file: str = "vG_default_params_HYDRUS.dat",
) -> list[LASAM]:
    """Creates the initial parameter estimates for the LASAM module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
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
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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
            soil_params_file=soil_params_file,  # TODO figure out why this exists?
            layer_soil_type=str(row_dict["soil_type"]),
            sft_coupled=sft_included,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_noahowp_parameters(
    catalog: Catalog, namespace: str, identifier: str, graph: rx.PyDiGraph
) -> list[NoahOwpModular]:
    """Creates the initial parameter estimates for the Noah OWP Modular module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier

    Returns
    -------
    list[NoahOwpModular]
        The list of all initial parameters for catchments using NoahOwpModular
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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
    for _, row_dict in result_df.iterrows():
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
    catalog: Catalog, namespace: str, identifier: str, envca: bool, graph: rx.PyDiGraph
) -> list[SacSma]:
    """Creates the initial parameter estimates for the SAC SMA module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier

    envca : bool, optional
        If source is ENVCA, then set to True - otherwise False.

    Returns
    -------
    list[SacSma]
        The list of all initial parameters for catchments using SacSma
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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

    if namespace == "conus_hf" and not envca:
        divides_list = result_df["divide_id"]
        domain = namespace.split("_")[0]
        table_name = f"divide_parameters.sac-sma_{domain}"
        params_df = catalog.load_table(table_name).to_polars()
        conus_param_df = params_df.filter(pl.col("divide_id").is_in(divides_list)).collect().to_pandas()
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
    for _, row_dict in result_df.iterrows():
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


def get_troute_parameters(
    catalog: Catalog, namespace: str, identifier: str, graph: rx.PyDiGraph
) -> list[TRoute]:
    """Creates the initial parameter estimates for the T-Route

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier

    Returns
    -------
    list[TRoute]
        The list of all initial parameters for catchments using TRoute
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
    )

    # Extraction of relevant features from divide attributes layer
    divide_attr_df = pd.DataFrame(gauge["divide-attributes"])
    nwtopo_param = collections.defaultdict(dict)
    nwtopo_param["supernetwork_parameters"].update({"geo_file_path": f"gauge_{identifier}.gpkg"})
    nwtopo_param["waterbody_parameters"].update(
        {"level_pool": {"level_pool_waterbody_parameter_file_path": f"gauge_{identifier}.gpkg"}}
    )

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        model_instance = TRoute(catchment=row_dict["divide_id"], nwtopo_param=nwtopo_param)
        pydantic_models.append(model_instance)
    return pydantic_models


def get_topmodel_parameters(
    catalog: Catalog, namespace: str, identifier: str, graph: rx.PyDiGraph
) -> list[Topmodel]:
    """Creates the initial parameter estimates for the Topmodel

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
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
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
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


def get_topoflow_parameters(
    catalog: Catalog, namespace: str, identifier: str, graph: rx.PyDiGraph
) -> list[Topoflow]:
    """Creates the initial parameter estimates for the Topoflow module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
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


def get_ueb_parameters(
    catalog: Catalog,
    namespace: str,
    identifier: str,
    envca: bool,
    graph: rx.PyDiGraph,
) -> list[UEB]:
    """Creates the initial parameter estimates for the UEB module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : HydrofabricDomains
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    envca : bool, optional
        If source is ENVCA, then set to True - otherwise False.

    Returns
    -------
    list[UEB]
        The list of all initial parameters for catchments using UEB
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
    )
    attr = {
        "slope": "mean.slope",
        "aspect": "circ_mean.aspect",
        "elevation": "mean.elevation",
        "lat": "centroid_y",
        "lon": "centroid_x",
    }

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = pl.DataFrame(gauge["divide-attributes"])
    expressions = [pl.col("divide_id")]
    for param_name, prefix in attr.items():
        # Find all columns that start with the prefix
        matching_cols = [col for col in divide_attr_df.columns if col == prefix]
        if matching_cols:
            expressions.append(pl.concat([pl.col(col) for col in matching_cols]).alias(f"{param_name}"))
        else:
            # Default to 0.0 if no matching columns found
            expressions.append(pl.lit(0.0).alias(f"{param_name}"))

    result_df = divide_attr_df.select(expressions).to_pandas()

    # Convert elevation from cm to m
    result_df["elevation"] = result_df["elevation"] * 0.01

    # Convert CRS to WGS84 (EPSG4326)
    crs = gauge["divides"].crs
    transformer = Transformer.from_crs(crs, 4326)
    wgs84_latlon = transformer.transform(result_df["lon"], result_df["lat"])
    result_df["lon"] = wgs84_latlon[0]
    result_df["lat"] = wgs84_latlon[1]

    # Default parameter values used only for CONUS
    result_df["jan_temp_range"] = UEBValues.JAN_TEMP.value
    result_df["feb_temp_range"] = UEBValues.FEB_TEMP.value
    result_df["mar_temp_range"] = UEBValues.MAR_TEMP.value
    result_df["apr_temp_range"] = UEBValues.APR_TEMP.value
    result_df["may_temp_range"] = UEBValues.MAY_TEMP.value
    result_df["jun_temp_range"] = UEBValues.JUN_TEMP.value
    result_df["jul_temp_range"] = UEBValues.JUL_TEMP.value
    result_df["aug_temp_range"] = UEBValues.AUG_TEMP.value
    result_df["sep_temp_range"] = UEBValues.SEP_TEMP.value
    result_df["oct_temp_range"] = UEBValues.OCT_TEMP.value
    result_df["nov_temp_range"] = UEBValues.NOV_TEMP.value
    result_df["dec_temp_range"] = UEBValues.DEC_TEMP.value

    if namespace == "conus_hf" and not envca:
        divides_list = result_df["divide_id"]
        domain = namespace.split("_")[0]
        table_name = f"divide_parameters.ueb_{domain}"
        params_df = catalog.load_table(table_name).to_polars()
        conus_param_df = params_df.filter(pl.col("divide_id").is_in(divides_list)).collect().to_pandas()
        col2drop = [col for col in result_df.columns if col.endswith("_temp_range")]
        result_df.drop(columns=col2drop, inplace=True)
        result_df = pd.merge(conus_param_df, result_df, on="divide_id", how="left")
        result_df.rename(
            columns={
                "b01": "jan_temp_range",
                "b02": "feb_temp_range",
                "b03": "mar_temp_range",
                "b04": "apr_temp_range",
                "b05": "may_temp_range",
                "b06": "jun_temp_range",
                "b07": "jul_temp_range",
                "b08": "aug_temp_range",
                "b09": "sep_temp_range",
                "b10": "oct_temp_range",
                "b11": "nov_temp_range",
                "b12": "dec_temp_range",
            },
            inplace=True,
        )

    pydantic_models = []
    for _, row_dict in result_df.iterrows():
        model_instance = UEB(
            catchment=row_dict["divide_id"],
            aspect=row_dict["aspect"],
            slope=row_dict["slope"],
            longitude=row_dict["lon"],
            latitude=row_dict["lat"],
            elevation=row_dict["elevation"],
            standard_atm_pressure=round(Atmosphere(row_dict["elevation"]).pressure[0], 4),
            jan_temp_range=row_dict["jan_temp_range"],
            feb_temp_range=row_dict["feb_temp_range"],
            mar_temp_range=row_dict["mar_temp_range"],
            apr_temp_range=row_dict["apr_temp_range"],
            may_temp_range=row_dict["may_temp_range"],
            jun_temp_range=row_dict["jun_temp_range"],
            jul_temp_range=row_dict["jul_temp_range"],
            aug_temp_range=row_dict["aug_temp_range"],
            sep_temp_range=row_dict["sep_temp_range"],
            oct_temp_range=row_dict["oct_temp_range"],
            nov_temp_range=row_dict["nov_temp_range"],
            dec_temp_range=row_dict["dec_temp_range"],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_cfe_parameters(
    catalog: Catalog,
    namespace: str,
    identifier: str,
    cfe_version: str,
    graph: rx.PyDiGraph,
    sft_included: bool = False,
) -> list[CFE]:
    """Creates the initial parameter estimates for the CFE module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : HydrofabricDomains
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    cfe_version: str
        the CFE module type (e.g. CFE-X, CFE-S) for which determines whether
        to use Shaake or Xinanjiang for surface partitioning.
    sft_included: bool
        True if SFT is in the "dep_modules_included" definition as declared in HF API repo.

    Returns
    -------
    list[CFE]
        The list of all initial parameters for catchments using CFE
    """
    gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
        catalog=catalog,
        identifier=identifier,
        id_type=IdType.HL_URI,
        namespace=namespace,
        layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
        graph=graph,
    )

    # CFE
    df = pd.DataFrame(gauge["divide-attributes"])
    divides_list = df["divide_id"]
    domain = namespace.split("_")[0]
    table_name = f"divide_parameters.cfe-x_{domain}"
    params_df = catalog.load_table(table_name).to_polars()
    conus_param_df = params_df.filter(pl.col("divide_id").is_in(divides_list)).collect().to_pandas()
    df = pd.merge(conus_param_df, df, on="divide_id", how="left")

    if cfe_version == "CFE-X":
        surface_partitioning_scheme = CFEValues.XINANJIANG.value
        urban_decimal_fraction = CFEValues.URBAN_FRACT.value
        is_sft_coupled = "NA"
    elif cfe_version == "CFE-S":
        surface_partitioning_scheme = CFEValues.SCHAAKE.value
        a_Xinanjiang_inflection_point_parameter = "NA"
        b_Xinanjiang_shape_parameter = "NA"
        x_Xinanjiang_shape_parameter = "NA"
        urban_decimal_fraction = "NA"
        if sft_included:
            is_sft_coupled = 1
        else:
            is_sft_coupled = 0
    else:
        raise ValueError(f"Passing unsupported cfe_version into endpoint: {cfe_version}")

    pydantic_models = []
    for _, row_dict in df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = CFE(
            catchment=row_dict["divide_id"],
            surface_partitioning_scheme=surface_partitioning_scheme,
            is_sft_coupled=str(is_sft_coupled),
            soil_params_b=row_dict["mode.bexp_soil_layers_stag=1"],
            soil_params_satdk=row_dict["geom_mean.dksat_soil_layers_stag=1"],
            soil_params_satpsi=row_dict["geom_mean.psisat_soil_layers_stag=1"],
            soil_params_slop=row_dict["mean.slope_1km"],
            soil_params_smcmax=row_dict["mean.smcmax_soil_layers_stag=1"],
            soil_params_wltsmc=row_dict["mean.smcwlt_soil_layers_stag=1"],
            max_gw_storage=row_dict["mean.Zmax"],
            Cgw=row_dict["mean.Coeff"],
            expon=row_dict["mode.Expon"],
            a_Xinanjiang_inflection_point_parameter=str(row_dict["a_Xinanjiang_inflection_point_parameter"])
            if cfe_version == "CFE-X"
            else a_Xinanjiang_inflection_point_parameter,
            b_Xinanjiang_shape_parameter=str(row_dict["b_Xinanjiang_shape_parameter"])
            if cfe_version == "CFE-X"
            else b_Xinanjiang_shape_parameter,
            x_Xinanjiang_shape_parameter=str(row_dict["x_Xinanjiang_shape_parameter"])
            if cfe_version == "CFE-X"
            else x_Xinanjiang_shape_parameter,
            urban_decimal_fraction=str(urban_decimal_fraction),
            refkdt=row_dict["mean.refkdt"],
        )
        pydantic_models.append(model_instance)
    return pydantic_models
