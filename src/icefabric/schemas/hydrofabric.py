"""Contains all schemas and enums for the NGWPC Enterprise Hydrofabric"""

from __future__ import annotations

from enum import Enum


class HydrofabricSource(str, Enum):
    """The hydrofabric data source to query.

    Attributes
    ----------
    NHF : str
        National Hydrofabric
    HF : str
        Hydrofabric v2.2
    """

    NHF = "nhf"
    HF = "hf"


class GeographicDomain(str, Enum):
    """NGWPC canonical geographic domain names for use with source parameter.

    Attributes
    ----------
    CONUS : str
        Conterminous United States
    ALASKA : str
        Alaska
    HAWAII : str
        Hawaii
    PUERTO_RICO : str
        Puerto Rico and US Virgin Islands
    GREAT_LAKES : str
        The US Great Lakes
    """

    CONUS = "CONUS"
    ALASKA = "Alaska"
    HAWAII = "Hawaii"
    PUERTO_RICO = "Puerto_Rico"
    GREAT_LAKES = "Great_Lakes"


class IdType(str, Enum):
    """All queriable HF fields.

    Attributes
    ----------
    HL_URI : str
        Hydrolocation URI identifier
    HF_ID : str
        Hydrofabric ID identifier
    ID : str
        Generic ID identifier
    POI_ID : str
        Point of Interest ID identifier
    """

    HL_URI = "hl_uri"
    HF_ID = "hf_id"
    ID = "id"
    POI_ID = "poi_id"
    VPU_ID = "vpu_id"
    FP_ID = ("fp_id",)
    SITE_NO = "site_no"


class HydrofabricDomains(str, Enum):
    """The domains used when querying the hydrofabric

    Attributes
    ----------
    AK : str
        Alaska
    CONUS : str
        Conterminous United States
    GL : str
        The US Great Lakes
    HI : str
        Hawai'i
    PRVI : str
        Puerto Rico, US Virgin Islands
    """

    AK = "ak_hf"
    CONUS = "conus_hf"
    GL = "gl_hf"
    HI = "hi_hf"
    PRVI = "prvi_hf"
    NHF = "nhf"

    @classmethod
    def _missing_(cls, value):
        """Accept user-friendly domain names as aliases."""
        aliases = {
            "CONUS": cls.CONUS,
            "Alaska": cls.AK,
            "Hawaii": cls.HI,
            "Puerto_Rico": cls.PRVI,
            "Great_Lakes": cls.GL,
        }
        return aliases.get(value)


class StreamflowDataSources(str, Enum):
    """The data sources used for hourly streamflow data"""

    USGS = "USGS"
    ENVCA = "ENVCA"
    CADWR = "CADWR"
    TXDOT = "TXDOT"


class StreamflowOutputFormats(str, Enum):
    """The data formats that the API/CLI can return for hourly streamflow data"""

    CSV = "csv"
    PARQUET = "parquet"

    def media_type(self):
        """Returns media type for the specified output format"""
        if self.value == "csv":
            return "text/csv"
        elif self.value == "parquet":
            return "application/vnd.apache.parquet"


# For catchments that may extend in many VPUs
UPSTREAM_VPUS: dict[str, list[str]] = {"08": ["11", "10U", "10L", "08", "07", "05"]}


# Mapping from GeographicDomain + HydrofabricSource to namespace
_DOMAIN_SOURCE_TO_NAMESPACE: dict[tuple[GeographicDomain, HydrofabricSource], str | None] = {
    (GeographicDomain.CONUS, HydrofabricSource.NHF): "nhf",
    (GeographicDomain.CONUS, HydrofabricSource.HF): "conus_hf",
    (GeographicDomain.ALASKA, HydrofabricSource.NHF): None,  # Not currently available
    (GeographicDomain.ALASKA, HydrofabricSource.HF): "ak_hf",
    (GeographicDomain.HAWAII, HydrofabricSource.NHF): None,  # Not currently available
    (GeographicDomain.HAWAII, HydrofabricSource.HF): "hi_hf",
    (GeographicDomain.PUERTO_RICO, HydrofabricSource.NHF): None,  # Not currently available
    (GeographicDomain.PUERTO_RICO, HydrofabricSource.HF): "prvi_hf",
    (GeographicDomain.GREAT_LAKES, HydrofabricSource.NHF): None,  # Not currently available
    (GeographicDomain.GREAT_LAKES, HydrofabricSource.HF): "gl_hf",
}

# Mapping from legacy HydrofabricDomains string values to namespace
_LEGACY_DOMAIN_TO_NAMESPACE: dict[str, str] = {
    "nhf": "nhf",
    "conus_hf": "conus_hf",
    "ak_hf": "ak_hf",
    "hi_hf": "hi_hf",
    "prvi_hf": "prvi_hf",
    "gl_hf": "gl_hf",
}


def resolve_namespace(
    domain: HydrofabricDomains | GeographicDomain | str | None,
    source: HydrofabricSource | None,
) -> tuple[str, bool, list[str]]:
    """
    Resolve domain/source to namespace

    Parameters
    ----------
    domain : HydrofabricDomains | GeographicDomain | str | None
        The domain to resolve. Can be a legacy HydrofabricDomains value,
        a new GeographicDomain value, or a string.
    source : HydrofabricSource | None
        The hydrofabric source (nhf or hf). Required when using GeographicDomain.

    Returns
    -------
    tuple[str, bool, list[str]]
        A tuple of (namespace, is_nhf, deprecated_warnings).
        - namespace: The resolved database namespace string
        - is_nhf: True if this is NHF data (for routing to correct service)
        - deprecated_warnings: Always empty list (kept for API compatibility)

    Raises
    ------
    ValueError
        If source is provided without domain, or if invalid combination is given.
    NotImplementedError
        If the domain is not available for the requested source (e.g., Alaska with NHF).
    """
    # Neither domain nor source provided - use default
    if domain is None and source is None:
        return "nhf", True, []

    # Source provided without domain - error
    if source is not None and domain is None:
        raise ValueError("When 'source' is provided, 'domain' must also be specified.")

    # Domain provided without source - legacy mode or default to HF
    if source is None and domain is not None:
        # Check if it's a GeographicDomain instance directly - default to HF
        if isinstance(domain, GeographicDomain):
            source = HydrofabricSource.HF
            # Fall through to the "both provided" case below
        else:
            # Get the string value of the domain
            domain_str = domain.value if isinstance(domain, HydrofabricDomains) else str(domain)

            # Check if it's a legacy domain value
            if domain_str in _LEGACY_DOMAIN_TO_NAMESPACE:
                namespace = _LEGACY_DOMAIN_TO_NAMESPACE[domain_str]
                is_nhf = namespace == "nhf"
                return namespace, is_nhf, []

            # Check if it's a geographic domain string without source - default to HF
            try:
                domain = GeographicDomain(domain_str)
                source = HydrofabricSource.HF
                # Fall through to the "both provided" case below
            except ValueError:
                raise ValueError(f"Unknown domain value: '{domain_str}'")

    # Both source and domain provided - new API
    # Convert domain to GeographicDomain
    # enum types checked first since HydrofabricDomains extends (str, Enum)
    if isinstance(domain, HydrofabricDomains):
        # User provided a legacy domain with source - convert to GeographicDomain
        legacy_to_geo = {
            HydrofabricDomains.CONUS: GeographicDomain.CONUS,
            HydrofabricDomains.AK: GeographicDomain.ALASKA,
            HydrofabricDomains.HI: GeographicDomain.HAWAII,
            HydrofabricDomains.PRVI: GeographicDomain.PUERTO_RICO,
            HydrofabricDomains.GL: GeographicDomain.GREAT_LAKES,
            HydrofabricDomains.NHF: GeographicDomain.CONUS,  # nhf maps to CONUS
        }
        domain = legacy_to_geo.get(domain, GeographicDomain.CONUS)
    elif isinstance(domain, str) and not isinstance(domain, GeographicDomain):
        # Plain string domain - convert to GeographicDomain
        try:
            domain = GeographicDomain(domain)
        except ValueError:
            raise ValueError(
                f"Invalid geographic domain '{domain}'. "
                f"Valid values are: {', '.join(d.value for d in GeographicDomain)}"
            )

    # Convert source to HydrofabricSource if it's a string
    if isinstance(source, str):
        try:
            source = HydrofabricSource(source)
        except ValueError:
            raise ValueError(f"Invalid source '{source}'. Valid values are: 'nhf', 'hf'")

    # At this point, domain must be a GeographicDomain and source must be HydrofabricSource
    if not isinstance(domain, GeographicDomain) or not isinstance(source, HydrofabricSource):
        raise ValueError("Internal error: domain and source must be resolved at this point")

    geo_domain: GeographicDomain = domain
    hf_source: HydrofabricSource = source

    # Look up the namespace
    namespace = _DOMAIN_SOURCE_TO_NAMESPACE.get((geo_domain, hf_source))

    if namespace is None:
        raise NotImplementedError(
            f"Domain '{geo_domain.value}' is not currently available for source '{hf_source.value}'. "
            f"Only 'CONUS' is available for the National Hydrofabric (nhf) at this time."
        )

    is_nhf = hf_source == HydrofabricSource.NHF
    return namespace, is_nhf, []
