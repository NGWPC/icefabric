import json

import geopandas as gpd
import numpy as np
import pandas as pd
import polars as pl
import rustworkx as rx
from ambiance import Atmosphere
from pyiceberg.catalog import Catalog
from pyproj import Transformer

from icefabric.hydrofabric import subset_hydrofabric, subset_nhf
from icefabric.modules.divide_attributes import DivideAttributesHF, DivideAttributesNHF
from icefabric.schemas.hydrofabric import HydrofabricNamespace, IdType
from icefabric.schemas.modules import (
    CFE,
    LASAM,
    LSTM,
    SFT,
    SMP,
    UEB,
    CalibratableScheme,
    CFEUnits,
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


def select_attr_names(namespace: HydrofabricNamespace) -> object:
    """Selects the NHF or HF divide attribute name enum based on the namespace

    Parameters
    ----------
    namespace : str
        The namespace containing conus_hf or nhf

    Returns
    -------
    object
        The enum for the selected hydrofabric
    """
    if namespace.is_oconus_hf:
        raise ValueError("subsets currently are not working for the HFv2.2 in OCONUS domains")
    if namespace.is_nhf:
        return DivideAttributesNHF
    else:
        return DivideAttributesHF


def get_subset(
    catalog: Catalog,
    identifier: str | float,
    namespace: HydrofabricNamespace,
    graph: rx.PyDiGraph | None = None,
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame]:
    """
    Return a subset from NHF or HF 2.2

    Parameters
    ----------
    catalog : Catalog
        PyIceberg catalog
    identifier : str | float
        The identifier to subset around
    namespace : str
        Domain name / namespace
    upstream_dict : Dict[str, Set[str]]
        Pre-computed upstream lookup dictionary

    Returns
    -------
    Dict[str, pd.DataFrame | gpd.GeoDataFrame]
        Dictionary of layer names to their subsetted dataframes
    """
    if namespace.is_oconus_hf:
        raise ValueError("subsets currently are not working for the HFv2.2 in OCONUS domains")
    if namespace.is_nhf:
        gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_nhf(
            gage_id=identifier,
            catalog=catalog,
            namespace=namespace,
        )
    else:
        gauge: dict[str, pd.DataFrame | gpd.GeoDataFrame] = subset_hydrofabric(
            catalog=catalog,
            identifier=identifier,
            id_type=IdType.HL_URI,
            namespace=namespace,
            layers=["flowpaths", "nexus", "divides", "divide-attributes", "network"],
            graph=graph,
        )
    return gauge


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
    namespace: HydrofabricNamespace,
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})
    attr_names = select_attr_names(namespace)

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Quartz doesn't exist in the HF2.2 divide attributes, use default value.
        if namespace.is_nhf:
            quartz_value = row_dict[attr_names.QUARTZ.value]
        else:
            quartz_value = 1.0
        # Instantiate the Pydantic model for each row
        model_instance = SFT(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            smcmax={"value": row_dict[attr_names.SMCMAX.value], "units": "m/m"},
            b={"value": row_dict[attr_names.BEXP.value], "units": None},
            satpsi={"value": row_dict[attr_names.PSISAT.value], "units": "m"},
            quartz={"value": quartz_value, "units": "m"},
            ice_fraction_scheme=IceFractionScheme.XINANJIANG
            if use_schaake is False
            else IceFractionScheme.SCHAAKE,
            soil_temperature={"value": [280.372, 280.372, 280.372, 280.372], "units": "K"},
            # Assuming 45 degrees in all layers. TODO: Fix this as this doesn't make sense
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_snow17_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, envca: bool, graph: rx.PyDiGraph
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Run HF2.2 specific items:
    if not namespace.is_nhf:
        # Get divide area from divides layer
        divides_df = gauge["divides"][[attr_names.DIVIDE_ID.value, attr_names.AREA.value]]
        divide_attr_df = pd.merge(divide_attr_df, divides_df, on="divide_id", how="left")

        # Convert elevation from cm to m
        divide_attr_df[attr_names.ELEVATION.value] = divide_attr_df[attr_names.ELEVATION.value] * 0.01

        # Convert CRS to WGS84 (EPSG4326)
        crs = gauge["divides"].crs
        transformer = Transformer.from_crs(crs, 4326)
        wgs84_latlon = transformer.transform(
            divide_attr_df[attr_names.X.value], divide_attr_df[attr_names.Y.value]
        )
        divide_attr_df[attr_names.Y.value] = wgs84_latlon[0]
        divide_attr_df[attr_names.X.value] = wgs84_latlon[1]

        # Get Snow17 parameters from Iceberg tables
        if not envca:
            divides_list = divide_attr_df[attr_names.DIVIDE_ID.value]
            domain = namespace.split("_")[0]
            table_name = f"divide_parameters.snow-17_{domain}"
            params_df = catalog.load_table(table_name).to_polars()
            conus_param_df = (
                params_df.filter(pl.col(attr_names.DIVIDE_ID.value).is_in(divides_list)).collect().to_pandas()
            )
            divide_attr_df = pd.merge(
                divide_attr_df, conus_param_df, on=attr_names.DIVIDE_ID.value, how="left"
            )
        else:
            # Attributes don't exist in the dataset for Canada
            divide_attr_df["mfmax"] = CalibratableScheme.MFMAX.value
            divide_attr_df["mfmin"] = CalibratableScheme.MFMIN.value
            divide_attr_df["uadj"] = CalibratableScheme.UADJ.value

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        model_instance = Snow17(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            hru_id=row_dict[attr_names.DIVIDE_ID.value],
            hru_area=row_dict[attr_names.AREA.value],
            latitude=row_dict[attr_names.Y.value],
            elev=row_dict[attr_names.ELEVATION.value],
            mfmax=row_dict[attr_names.MFMAX.value],
            mfmin=row_dict[attr_names.MFMIN.value],
            uadj=row_dict[attr_names.UADJ.value],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_smp_parameters(
    catalog: Catalog,
    namespace: HydrofabricNamespace,
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Initializing parameters dependent to unique modules
    soil_storage_model = None
    soil_storage_depth = None
    water_table_based_method = None
    soil_moisture_profile_option = None
    soil_depth_layers = None
    water_depth_layers = None
    water_table_depth = None

    if extra_module:
        if extra_module == "CFE-S" or extra_module == "CFE-X":
            soil_storage_model = SoilScheme.CFE_SOIL_STORAGE.value
            soil_storage_depth = {"value": SoilScheme.CFE_STORAGE_DEPTH.value, "units": "m"}
        elif extra_module == "TopModel":
            soil_storage_model = SoilScheme.TOPMODEL_SOIL_STORAGE.value
            water_table_based_method = SoilScheme.TOPMODEL_WATER_TABLE_METHOD.value
        elif extra_module == "LASAM":
            soil_storage_model = SoilScheme.LASAM_SOIL_STORAGE.value
            soil_moisture_profile_option = SoilScheme.LASAM_SOIL_MOISTURE.value
            soil_depth_layers = {"value": SoilScheme.LASAM_SOIL_DEPTH_LAYERS.value, "units": "m"}
            water_table_depth = {"value": SoilScheme.LASAM_WATER_TABLE_DEPTH.value, "units": "m"}
        else:
            raise ValueError(f"Passing unsupported module into endpoint: {extra_module}")

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = SMP(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            smcmax={"value": row_dict[attr_names.SMCMAX.value], "units": "m/m"},
            b={"value": row_dict[attr_names.BEXP.value], "units": None},
            satpsi={"value": row_dict[attr_names.PSISAT.value], "units": "m"},
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


def get_lstm_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, graph: rx.PyDiGraph
) -> list[LSTM]:
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Run HF2.2 specific items
    if not namespace.is_nhf:
        # Get divide area from divides layer
        divides_df = gauge["divides"][[attr_names.DIVIDE_ID.value, attr_names.AREA.value]]
        divide_attr_df = pd.merge(divide_attr_df, divides_df, on=attr_names.DIVIDE_ID.value, how="left")

        # Convert elevation from cm to m
        divide_attr_df[attr_names.ELEVATION.value] = divide_attr_df[attr_names.ELEVATION.value] * 0.01

        # Convert CRS to WGS84 (EPSG4326)
        crs = gauge["divides"].crs
        transformer = Transformer.from_crs(crs, 4326)
        wgs84_latlon = transformer.transform(
            divide_attr_df[attr_names.X.value], divide_attr_df[attr_names.Y.value]
        )
        divide_attr_df[attr_names.Y.value] = wgs84_latlon[0]
        divide_attr_df[attr_names.X.value] = wgs84_latlon[1]

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = LSTM(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            area_sqkm=row_dict[attr_names.AREA.value],
            basin_id=identifier,
            elev_mean=row_dict[attr_names.ELEVATION.value],
            lat=row_dict[attr_names.Y.value],
            lon=row_dict[attr_names.X.value],
            slope_mean=row_dict[attr_names.SLOPE.value],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_lasam_parameters(
    catalog: Catalog,
    namespace: HydrofabricNamespace,
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = LASAM(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            soil_params_file=soil_params_file,  # TODO figure out why this exists?
            layer_soil_type=str(row_dict[attr_names.ISLTYP.value]),
            sft_coupled=sft_included,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_noahowp_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, graph: rx.PyDiGraph
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Convert CRS to WGS84 (EPSG4326) for HF2.2
    if not namespace.is_nhf:
        crs = gauge["divides"].crs
        transformer = Transformer.from_crs(crs, 4326)
        wgs84_latlon = transformer.transform(
            divide_attr_df[attr_names.X.value], divide_attr_df[attr_names.Y.value]
        )
        divide_attr_df[attr_names.Y.value] = wgs84_latlon[0]
        divide_attr_df[attr_names.X.value] = wgs84_latlon[1]

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = NoahOwpModular(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            lat=row_dict[attr_names.Y.value],
            lon=row_dict[attr_names.X.value],
            terrain_slope=row_dict[attr_names.SLOPE.value],
            azimuth=row_dict[attr_names.ASPECT.value],
            isltyp=row_dict[attr_names.ISLTYP.value],
            vegtyp=row_dict[attr_names.IVGTYP.value],
            sfctyp=2 if row_dict[attr_names.IVGTYP.value] == 16 else 1,
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_sacsma_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, envca: bool, graph: rx.PyDiGraph
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    attr_names = select_attr_names(namespace)

    # Extraction of relevant features from divides layer
    pd.options.mode.chained_assignment = None

    if namespace.is_nhf:
        result_df = pd.DataFrame(gauge["divides"])
    else:
        result_df = gauge["divides"][[attr_names.DIVIDE_ID.value, attr_names.AREA.value]]
        if not envca:
            divides_list = result_df[attr_names.DIVIDE_ID.value]
            domain = namespace.split("_")[0]
            table_name = f"divide_parameters.sac-sma_{domain}"
            params_df = catalog.load_table(table_name).to_polars()
            conus_param_df = (
                params_df.filter(pl.col(attr_names.DIVIDE_ID.value).is_in(divides_list)).collect().to_pandas()
            )
            result_df = pd.merge(conus_param_df, result_df, on=attr_names.DIVIDE_ID.value, how="left")
        else:
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

    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    result_df = result_df.replace({np.nan: None})

    pydantic_models = []
    for _, row_dict in result_df.iterrows():
        # Instantiate the Pydantic model for each row
        # *Note: The HF API declares hru_id as the divide id, but to remain consistent
        # keeping catchment arg.
        model_instance = SacSma(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            hru_id=row_dict[attr_names.DIVIDE_ID.value],
            hru_area=row_dict[attr_names.AREA.value],
            uztwm=row_dict[attr_names.UZTWM.value],
            uzfwm=row_dict[attr_names.UZFWM.value],
            lztwm=row_dict[attr_names.LZTWM.value],
            lzfpm=row_dict[attr_names.LZFPM.value],
            lzfsm=row_dict[attr_names.LZFSM.value],
            uzk=row_dict[attr_names.UZK.value],
            lzpk=row_dict[attr_names.LZPK.value],
            lzsk=row_dict[attr_names.LZSK.value],
            zperc=row_dict[attr_names.ZPERC.value],
            rexp=row_dict[attr_names.REXP.value],
            pfree=row_dict[attr_names.PFREE.value],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_troute_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, graph: rx.PyDiGraph
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
        The list of TRoute parameters for the gauge.
    """
    pydantic_models = TRoute()

    # Add geopackage filename
    gpkg_string = f"hydrofabric_subset_{identifier}_site_no.gpkg"
    pydantic_models.network_topology_parameters["supernetwork_parameters"]["geo_file_path"] = gpkg_string
    pydantic_models.network_topology_parameters["waterbody_parameters"]["level_pool"][
        "level_pool_waterbody_parameter_file_path"
    ] = gpkg_string

    return [pydantic_models]


def get_topmodel_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, graph: rx.PyDiGraph
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
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Get flowpath length from divides layer for HF2.2 or from flowpaths layer in NHF
    if namespace.is_nhf:
        flowpaths_df = pd.DataFrame(gauge["flowpaths"])[
            [attr_names.DIVIDE_ID.value, attr_names.FLOWPATH_LENGTH.value]
        ]
    else:
        flowpaths_df = pd.DataFrame(gauge["divides"])[
            [attr_names.DIVIDE_ID.value, attr_names.FLOWPATH_LENGTH.value]
        ]

    divide_attr_df = pd.merge(divide_attr_df, flowpaths_df, on=attr_names.DIVIDE_ID.value, how="left")

    pydantic_models = []
    for _idx, row_dict in divide_attr_df.iterrows():
        if namespace.is_nhf:
            twi_json = [
                {"v": row_dict[attr_names.TWI_Q25.value], "Frequency": "0.25"},
                {"v": row_dict[attr_names.TWI_Q50.value], "Frequency": "0.25"},
                {"v": row_dict[attr_names.TWI_Q75.value], "Frequency": "0.25"},
                {"v": row_dict[attr_names.TWI_Q100.value], "Frequency": "0.25"},
            ]
        else:
            twi_json = json.loads(row_dict[attr_names.TWI.value])

        model_instance = Topmodel(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            divide_id=row_dict[attr_names.DIVIDE_ID.value],
            twi=twi_json,
            num_topodex_values=len(twi_json),
            dist_from_outlet=round(row_dict[attr_names.FLOWPATH_LENGTH.value] * 1000),
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_topoflow_parameters(
    catalog: Catalog, namespace: HydrofabricNamespace, identifier: str, graph: rx.PyDiGraph
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
    """
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Run items specifically for HF2.2
    if not namespace.is_nhf:
        divides_df = gauge["divides"][[attr_names.DIVIDE_ID.value, attr_names.AREA.value]]
        divide_attr_df = divide_attr_df.merge(divides_df, on=attr_names.DIVIDE_ID.value, how="left")

        # Convert elevation from cm to m
        divide_attr_df[attr_names.ELEVATION.value] = divide_attr_df[attr_names.ELEVATION.value] * 0.01

        # Convert CRS to WGS84 (EPSG4326)
        crs = gauge["divides"].crs
        transformer = Transformer.from_crs(crs, 4326)
        wgs84_latlon = transformer.transform(
            divide_attr_df[attr_names.X.value], divide_attr_df[attr_names.Y.value]
        )
        divide_attr_df[attr_names.Y.value] = wgs84_latlon[0]
        divide_attr_df[attr_names.X.value] = wgs84_latlon[1]

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        model_instance = Topoflow(
            site_prefix=row_dict[attr_names.DIVIDE_ID.value],
            forcing_file=f"data/{row_dict[attr_names.DIVIDE_ID.value]}.csv",
            da=row_dict[attr_names.AREA.value],
            slope=row_dict[attr_names.SLOPE.value],
            aspect=row_dict[attr_names.ASPECT.value],
            lon=row_dict[attr_names.X.value],
            lat=row_dict[attr_names.Y.value],
            elev=row_dict[attr_names.ELEVATION.value],
            glacier_percent=row_dict[attr_names.GLACIER_PERCENT.value],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_ueb_parameters(
    catalog: Catalog,
    namespace: HydrofabricNamespace,
    identifier: str,
    envca: bool,
    graph: rx.PyDiGraph,
) -> list[UEB]:
    """Creates the initial parameter estimates for the UEB module

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
    list[UEB]
        The list of all initial parameters for catchments using UEB
    """
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    # Extraction of relevant features from divide attributes layer
    # & convert to polar
    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})

    attr_names = select_attr_names(namespace)

    # Run items specifically for HF2.2
    if not namespace.is_nhf:
        # Convert elevation from cm to m
        divide_attr_df[attr_names.ELEVATION.value] = divide_attr_df[attr_names.ELEVATION.value] * 0.01

        # Convert CRS to WGS84 (EPSG4326)
        crs = gauge["divides"].crs
        transformer = Transformer.from_crs(crs, 4326)
        wgs84_latlon = transformer.transform(
            divide_attr_df[attr_names.X.value], divide_attr_df[attr_names.Y.value]
        )
        divide_attr_df[attr_names.Y.value] = wgs84_latlon[0]
        divide_attr_df[attr_names.X.value] = wgs84_latlon[1]

        # Get temperature values from Iceberg tables
        if not envca:
            divides_list = divide_attr_df[attr_names.DIVIDE_ID.value]
            domain = namespace.split("_")[0]
            table_name = f"divide_parameters.ueb_{domain}"
            params_df = catalog.load_table(table_name).to_polars()
            conus_param_df = (
                params_df.filter(pl.col(attr_names.DIVIDE_ID.value).is_in(divides_list)).collect().to_pandas()
            )
            col2drop = [col for col in divide_attr_df.columns if col.endswith("_temp_range")]
            divide_attr_df.drop(columns=col2drop, inplace=True)
            divide_attr_df = pd.merge(
                conus_param_df, divide_attr_df, on=attr_names.DIVIDE_ID.value, how="left"
            )
            divide_attr_df.rename(
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
        else:
            # Default parameter values
            divide_attr_df["jan_temp_range"] = UEBValues.JAN_TEMP.value
            divide_attr_df["feb_temp_range"] = UEBValues.FEB_TEMP.value
            divide_attr_df["mar_temp_range"] = UEBValues.MAR_TEMP.value
            divide_attr_df["apr_temp_range"] = UEBValues.APR_TEMP.value
            divide_attr_df["may_temp_range"] = UEBValues.MAY_TEMP.value
            divide_attr_df["jun_temp_range"] = UEBValues.JUN_TEMP.value
            divide_attr_df["jul_temp_range"] = UEBValues.JUL_TEMP.value
            divide_attr_df["aug_temp_range"] = UEBValues.AUG_TEMP.value
            divide_attr_df["sep_temp_range"] = UEBValues.SEP_TEMP.value
            divide_attr_df["oct_temp_range"] = UEBValues.OCT_TEMP.value
            divide_attr_df["nov_temp_range"] = UEBValues.NOV_TEMP.value
            divide_attr_df["dec_temp_range"] = UEBValues.DEC_TEMP.value

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        model_instance = UEB(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            aspect=row_dict[attr_names.ASPECT.value],
            slope=row_dict[attr_names.SLOPE.value],
            longitude=row_dict[attr_names.X.value],
            latitude=row_dict[attr_names.Y.value],
            elevation=row_dict[attr_names.ELEVATION.value],
            standard_atm_pressure=round(Atmosphere(row_dict[attr_names.ELEVATION.value]).pressure[0], 4),
            jan_temp_range=row_dict[attr_names.JAN.value],
            feb_temp_range=row_dict[attr_names.FEB.value],
            mar_temp_range=row_dict[attr_names.MAR.value],
            apr_temp_range=row_dict[attr_names.APR.value],
            may_temp_range=row_dict[attr_names.MAY.value],
            jun_temp_range=row_dict[attr_names.JUN.value],
            jul_temp_range=row_dict[attr_names.JUL.value],
            aug_temp_range=row_dict[attr_names.AUG.value],
            sep_temp_range=row_dict[attr_names.SEP.value],
            oct_temp_range=row_dict[attr_names.OCT.value],
            nov_temp_range=row_dict[attr_names.NOV.value],
            dec_temp_range=row_dict[attr_names.DEC.value],
        )
        pydantic_models.append(model_instance)
    return pydantic_models


def get_cfe_parameters(
    catalog: Catalog,
    namespace: HydrofabricNamespace,
    identifier: str,
    cfe_version: str,
    graph: rx.PyDiGraph | None = None,
    sft_included: bool = False,
    rootzone_aet: bool = False,
) -> list[CFE]:
    """Creates the initial parameter estimates for the CFE module

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg lakehouse catalog
    namespace : str
        the hydrofabric namespace
    identifier : str
        the gauge identifier
    cfe_version: str
        the CFE module type (e.g. CFE-X, CFE-S) for which determines whether
        to use Shaake or Xinanjiang for surface partitioning.
    sft_included: bool
        True if SFT is in the "dep_modules_included" definition as declared in HF API repo.
    rootzone_aet: bool
        Turn on rootzone based AET (actual evapotranspiration)

    Returns
    -------
    list[CFE]
        The list of all initial parameters for catchments using CFE
    """
    gauge = get_subset(catalog=catalog, identifier=identifier, namespace=namespace, graph=graph)

    divide_attr_df = (
        pd.DataFrame(gauge["divide-attributes"]) if not namespace.is_nhf else pd.DataFrame(gauge["divides"])
    )
    # Replace any NaNs in dataframe with None so it can be converted to JSON by FastAPI
    divide_attr_df = divide_attr_df.replace({np.nan: None})
    attr_names = select_attr_names(namespace)
    divides_list = divide_attr_df[attr_names.DIVIDE_ID.value]

    if not namespace.is_nhf:
        domain = namespace.split("_")[0]
        table_name = f"divide_parameters.cfe-x_{domain}"
        params_df = catalog.load_table(table_name).to_polars()
        conus_param_df = (
            params_df.filter(pl.col(attr_names.DIVIDE_ID.value).is_in(divides_list)).collect().to_pandas()
        )
        divide_attr_df = pd.merge(conus_param_df, divide_attr_df, on=attr_names.DIVIDE_ID.value, how="left")

    if rootzone_aet:
        is_aet_rootzone = True
        soil_layer_depths = {"value": CFEValues.SOIL_LAYER_DEPTHS.value, "units": CFEUnits.SOIL_DEPTH.value}
        max_rootzone_layer = {
            "value": CFEValues.MAX_ROOTZONE_LAYER.value,
            "units": CFEUnits.MAX_ROOTZONE_LAYER.value,
        }
    else:
        is_aet_rootzone = False
        soil_layer_depths = None
        max_rootzone_layer = None

    if cfe_version == "CFE-X":
        surface_partitioning_scheme = CFEValues.XINANJIANG.value
        urban_decimal_fraction = {"value": CFEValues.URBAN_FRACT.value, "units": CFEUnits.URBAN_FRACT.value}
        ice_content_thresh = None
        if sft_included:
            is_sft_coupled = True
        else:
            is_sft_coupled = False
    elif cfe_version == "CFE-S":
        surface_partitioning_scheme = CFEValues.SCHAAKE.value
        urban_decimal_fraction = None
        a_Xinanjiang_inflection_point_parameter = None
        b_Xinanjiang_shape_parameter = None
        x_Xinanjiang_shape_parameter = None
        if sft_included:
            is_sft_coupled = True
            ice_content_thresh = {
                "value": CFEValues.ICE_CONTENT_THR.value,
                "units": CFEUnits.ICE_CONTENT_THR.value,
            }
        else:
            is_sft_coupled = False
            ice_content_thresh = None
    else:
        raise ValueError(f"Passing unsupported cfe_version into endpoint: {cfe_version}")

    pydantic_models = []
    for _, row_dict in divide_attr_df.iterrows():
        # Instantiate the Pydantic model for each row
        if cfe_version == "CFE-X":
            a_Xinanjiang_inflection_point_parameter = {
                "value": row_dict[attr_names.AXAJ.value],
                "units": CFEUnits.A_XINANJIANG_INFLECT.value,
            }
            b_Xinanjiang_shape_parameter = {
                "value": row_dict[attr_names.BXAJ.value],
                "units": CFEUnits.B_XINANJIANG_SHAPE.value,
            }
            x_Xinanjiang_shape_parameter = {
                "value": row_dict[attr_names.XXAJ.value],
                "units": CFEUnits.X_XINANJIANG_SHAPE.value,
            }
            urban_decimal_fraction = {
                "value": row_dict[attr_names.IMPERVIOUS.value],
                "units": CFEUnits.URBAN_FRACT.value,
            }

        model_instance = CFE(
            catchment=row_dict[attr_names.DIVIDE_ID.value],
            surface_water_partitioning_scheme=surface_partitioning_scheme,
            is_sft_coupled=str(is_sft_coupled),
            ice_content_threshold=ice_content_thresh,
            soil_params_b={"value": row_dict[attr_names.BEXP.value], "units": CFEUnits.SOIL_B.value},
            soil_params_satdk={
                "value": row_dict[attr_names.DKSAT.value],
                "units": CFEUnits.SOIL_SATDK.value,
            },
            soil_params_satpsi={
                "value": row_dict[attr_names.PSISAT.value],
                "units": CFEUnits.SOIL_SATPSI.value,
            },
            soil_params_slop={
                "value": row_dict[attr_names.SLOPE_1KM.value],
                "units": CFEUnits.SOIL_SLOP.value,
            },
            soil_params_smcmax={
                "value": row_dict[attr_names.SMCMAX.value],
                "units": CFEUnits.SOIL_SMCMAX.value,
            },
            soil_params_wltsmc={
                "value": row_dict[attr_names.SMCWLT.value],
                "units": CFEUnits.SOIL_WLTSMC.value,
            },
            max_gw_storage={
                "value": row_dict[attr_names.ZMAX.value],
                "units": CFEUnits.MAX_GW_STORAGE.value,
            },
            Cgw={"value": row_dict[attr_names.COEFF.value], "units": CFEUnits.CGW.value},
            expon={"value": row_dict[attr_names.EXPON.value], "units": CFEUnits.EXPON.value},
            a_Xinanjiang_inflection_point_parameter=a_Xinanjiang_inflection_point_parameter,
            b_Xinanjiang_shape_parameter=b_Xinanjiang_shape_parameter,
            x_Xinanjiang_shape_parameter=x_Xinanjiang_shape_parameter,
            urban_decimal_fraction=urban_decimal_fraction,
            refkdt={"value": row_dict[attr_names.REFKDT.value], "units": CFEUnits.REFKDT.value},
            is_aet_rootzone=is_aet_rootzone,
            soil_layer_depths=soil_layer_depths,
            max_rootzone_layer=max_rootzone_layer,
        )

        pydantic_models.append(model_instance)
    return pydantic_models
