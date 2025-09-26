import httpx
import ipywidgets as widgets
import matplotlib.pyplot as plt
import pandas as pd
from pyiceberg import expressions
from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.exceptions import NoSuchTableError

from icefabric.schemas.hydrofabric import HydrofabricDomains


def get_streamflow_data(
    catalog_name: str,
    gage_id: str | None = None,
    row_filter: str | None = None,
    snapshot_id: int | None = None,
    **kwargs,
) -> pd.DataFrame:
    """Gets streamflow data for the Jupyter UI to display

    Parameters
    ----------
    gage_id : str
        The gauge ID you are looking to view
    catalog_name : str, optional
        The pyiceberg catalog name
    row_filter : str | None, optional
        The row filter to specify a start/end time, by default None
    snapshot_id : int | None, optional
        the snapshot ID to , by default None
    **kwargs
        the pyiceberg.yaml file settings

    Returns
    -------
    pd.DataFrame
        The streamflow output for the specified gauge

    Raises
    ------
    NoSuchTableError
        There is no existing record for the streamflow values
    """
    catalog = load_catalog(
        name=catalog_name,
        type=kwargs[catalog_name]["type"],
        uri=kwargs[catalog_name]["uri"],
        warehouse=kwargs[catalog_name]["warehouse"],
    )
    try:
        table = catalog.load_table("streamflow_observations.usgs_hourly")
        if row_filter is None:
            df = table.scan(snapshot_id=snapshot_id).to_pandas()
        else:
            df = table.scan(row_filter=row_filter, snapshot_id=snapshot_id).to_pandas()
        if gage_id is not None:
            return df[["time", gage_id]]
        else:
            return df
    except NoSuchTableError as e:
        msg = "No table/namespace found for streamflow_observations.usgs_hourly in the catalog"
        print(msg)
        raise NoSuchTableError from e


def get_hydrofabric_gages(
    catalog: Catalog, domain: HydrofabricDomains = HydrofabricDomains.CONUS
) -> list[str]:
    """Returns the hydrofabric gages within the network table

    Parameters
    ----------
    catalog : Catalog
        the pyiceberg warehouse reference
    domain : HydrofabricDomains, optional
        the hydrofabric domain, by default HydrofabricDomains.CONUS

    Returns
    -------
    list[str]
        The list of all gages in the conus-hf
    """
    return (
        catalog.load_table(f"{domain.value}.network")
        .scan(row_filter=expressions.StartsWith("hl_uri", "gages-"))
        .to_pandas()
        .drop_duplicates(subset="hl_uri", keep="first")[("hl_uri")]
        .tolist()
    )


def get_observational_uri(
    gage_id: str, source: str = "USGS", domain: str = "CONUS", version: str = "2.1", timeout=None
) -> str:
    """Fetch observational data URI from the NextGen Water Prediction API.

    Retrieves the URI for observational streamflow data for a specific gage
    from the NextGen Water Prediction hydrofabric API.

    Parameters
    ----------
    gage_id : str
        The gage identifier (e.g., USGS station ID).
    source : str, default "USGS"
        Data source provider for the observational data.
    domain : str, default "CONUS"
        Geographic domain name for the data request.
    version : str, default "2.1"
        API version to use for the request.
    timeout : float or None, optional
        Request timeout in seconds. If None, uses httpx default.

    Returns
    -------
    str
        The URI pointing to the observational dataset.
    """
    base_url = f"https://hydroapi.oe.nextgenwaterprediction.com/hydrofabric/{version}/observational"
    params = {"gage_id": gage_id, "source": source, "domain": domain}

    response = httpx.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()  # Raise an error if request failed
    data = response.json()

    return data["uri"]


def get_geopackage_uri(
    gage_id: str, source: str = "USGS", domain: str = "CONUS", version: str = "2.2", timeout=None
) -> str:
    """Fetch GeoPackage URI for a gage from the NextGen Water Prediction API.

    Retrieves the URI for a hydrofabric GeoPackage containing network topology
    and catchment boundaries for a specific gage from the NextGen API.

    Parameters
    ----------
    gage_id : str
        The gage identifier for which to retrieve the hydrofabric GeoPackage.
    source : str, default "USGS"
        Data source provider for the gage data.
    domain : str, default "CONUS"
        Geographic domain name for the hydrofabric request.
    version : str, default "2.2"
        Hydrofabric version to retrieve.
    timeout : float or None, optional
        Request timeout in seconds. If None, uses httpx default.

    Returns
    -------
    str
        The URI pointing to the GeoPackage file in S3 storage.
    """
    base_url = "https://hydroapi.oe.nextgenwaterprediction.com/hydrofabric/geopackages"
    params = {"gage_id": gage_id, "source": source, "domain": domain, "version": version}

    response = httpx.get(base_url, params=params, timeout=timeout)
    response.raise_for_status()
    data = response.json()

    return data["uri"]


def create_time_series_widget(
    df: pd.DataFrame, flow_col: str, point_size: float = 30, time_col: str = "time"
):
    """
    Creates an interactive time series plot using matplotlib and ipywidgets.

    Parameters
    ----------
        df (pd.DataFrame): DataFrame with 'DateTime' and 'q_cms' columns
        start_slider (widgets.SelectionSlider): Widget for selecting start time
        end_slider (widgets.SelectionSlider): Widget for selecting end time
    """
    start_slider = widgets.SelectionSlider(
        options=df["time"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        description="Start:",
        layout=widgets.Layout(width="95%"),
    )

    end_slider = widgets.SelectionSlider(
        options=df["time"].dt.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        description="End:",
        layout=widgets.Layout(width="95%"),
    )

    @widgets.interact(start=start_slider, end=end_slider)
    def plot_flow(start, end):
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)

        if start_dt >= end_dt:
            print("Warning: Start must be before End.")
            return

        filtered = df[(df[time_col] >= start_dt) & (df[time_col] <= end_dt)]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(filtered[time_col], filtered[flow_col], s=point_size, label="Flow rate (cms)", alpha=0.7)
        ax.set_xlabel("Date Time")
        ax.set_ylabel("Discharge (cms)")
        ax.set_title("Streamflow Time Series (Scatter Plot)")
        ax.grid(True)
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
