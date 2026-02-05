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

    @classmethod
    def _missing_(cls, value):
        """Accept legacy HF domain names as aliases.

        Note: 'nhf' is intentionally not mapped here because it implies
        the NHF source, not just a geographic domain.
        """
        aliases = {
            "conus_hf": cls.CONUS,
            "ak_hf": cls.ALASKA,
            "hi_hf": cls.HAWAII,
            "prvi_hf": cls.PUERTO_RICO,
            "gl_hf": cls.GREAT_LAKES,
        }
        return aliases.get(value)


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

# Namespace constants for internal use
NHF_NAMESPACES: set[str] = {"nhf", "conus_nhf"}
OCONUS_HF_NAMESPACES: set[str] = {"gl_hf", "ak_hf", "prvi_hf"}
ALL_HF_NAMESPACES: set[str] = {"conus_hf", "ak_hf", "hi_hf", "prvi_hf", "gl_hf"}


# Mapping from GeographicDomain + HydrofabricSource to namespace
_DOMAIN_SOURCE_TO_NAMESPACE: dict[tuple[GeographicDomain, HydrofabricSource], str | None] = {
    (GeographicDomain.CONUS, HydrofabricSource.NHF): "conus_nhf",
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
    domain: GeographicDomain | str | None,
    source: HydrofabricSource | None,
) -> tuple[str, bool, list[str]]:
    """
    Resolve domain/source to namespace

    Parameters
    ----------
    domain : GeographicDomain | str | None
        The domain to resolve. Can be a GeographicDomain value, a legacy string
        value (nhf, conus_hf, etc.), or a geographic domain string (CONUS, Alaska, etc.).
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
            domain_str = str(domain)

            # Check if it's a legacy domain value
            if domain_str in _LEGACY_DOMAIN_TO_NAMESPACE:
                namespace = _LEGACY_DOMAIN_TO_NAMESPACE[domain_str]
                is_nhf = namespace in NHF_NAMESPACES
                return namespace, is_nhf, []

            # Check if it's a geographic domain string without source - default to HF
            try:
                domain = GeographicDomain(domain_str)
                source = HydrofabricSource.HF
                # Fall through to the "both provided" case below
            except ValueError:
                raise ValueError(f"Unknown domain value: '{domain_str}'")

    # Both source and domain provided - new API
    # Convert domain to GeographicDomain if it's a string
    if isinstance(domain, str) and not isinstance(domain, GeographicDomain):
        # Check if it's a legacy domain string with source provided
        # Map legacy domain strings to GeographicDomain
        legacy_str_to_geo = {
            "conus_hf": GeographicDomain.CONUS,
            "ak_hf": GeographicDomain.ALASKA,
            "hi_hf": GeographicDomain.HAWAII,
            "prvi_hf": GeographicDomain.PUERTO_RICO,
            "gl_hf": GeographicDomain.GREAT_LAKES,
            "nhf": GeographicDomain.CONUS,  # nhf maps to CONUS
        }
        if domain in legacy_str_to_geo:
            domain = legacy_str_to_geo[domain]
        else:
            # Try as a GeographicDomain value
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
