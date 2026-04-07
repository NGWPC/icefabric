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
    ID : str
        Generic ID identifier
    """

    HL_URI = "hl_uri"  # HF 2.2 only
    ID = "id"  # HF 2.2 only
    POI_ID = "poi_id"  # HF 2.2 only


class QueryIdType(str, Enum):
    """All query types for the API.

    Attributes
    ----------
    GAGE_ID : str
        Gage ID query identifier
    FLOWPATH_ID : str
        Flowpath ID query identifier
    VPU_ID : str
         VPU ID query identifier
    """

    GAGE_ID = "gage_id"
    FLOWPATH_ID = "flowpath_id"
    VPU_ID = "vpu_id"


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


class HydrofabricNamespace(str, Enum):
    """All valid hydrofabric namespace values.

    Attributes
    ----------
    NHF : str
        Legacy NHF namespace (CONUS only)
    CONUS_NHF : str
        CONUS National Hydrofabric
    CONUS_HF : str
        CONUS Hydrofabric v2.2
    ALASKA_HF : str
        Alaska Hydrofabric v2.2
    HAWAII_HF : str
        Hawaii Hydrofabric v2.2
    PUERTO_RICO_HF : str
        Puerto Rico Hydrofabric v2.2
    GREAT_LAKES_HF : str
        Great Lakes Hydrofabric v2.2
    """

    NHF = "nhf"
    CONUS_NHF = "conus_nhf"
    ALASKA_NHF = "ak_nhf"
    HAWAII_NHF = "hi_nhf"
    PUERTO_RICO_NHF = "prvi_nhf"
    CONUS_HF = "conus_hf"
    ALASKA_HF = "ak_hf"
    HAWAII_HF = "hi_hf"
    PUERTO_RICO_HF = "prvi_hf"
    GREAT_LAKES_HF = "gl_hf"
    # Test-only namespace for unit tests with mock data
    MOCK_HF = "mock_hf"

    def __str__(self) -> str:
        """Return the string value for use in f-strings and str().

        In Python 3.11+, str(Enum) returns the member name (e.g., "HydrofabricNamespace.NHF")
        instead of the value, even for str-based enums. This override ensures f-strings like
        f"{namespace}.network" produce "nhf.network" rather than "HydrofabricNamespace.NHF.network".
        """
        return self.value

    @property
    def is_nhf(self) -> bool:
        """Return True if this namespace is NHF data."""
        return self in (
            HydrofabricNamespace.NHF,
            HydrofabricNamespace.CONUS_NHF,
            HydrofabricNamespace.ALASKA_NHF,
            HydrofabricNamespace.HAWAII_NHF,
            HydrofabricNamespace.PUERTO_RICO_NHF,
        )

    @property
    def is_oconus_hf(self) -> bool:
        """Return True if this namespace is OCONUS HF v2.2 data."""
        return self in (
            HydrofabricNamespace.ALASKA_HF,
            HydrofabricNamespace.PUERTO_RICO_HF,
            HydrofabricNamespace.GREAT_LAKES_HF,
        )

    @property
    def crs(self) -> str:
        """Return the EPSG CRS string for this namespace's native geometries.

        NHF geometries are ingested without reprojection, so the CRS differs by
        domain and must be re-applied when reading WKB back out of Iceberg.
        """
        oconus_nhf_crs = {
            HydrofabricNamespace.ALASKA_NHF: "EPSG:3338",
            HydrofabricNamespace.HAWAII_NHF: "EPSG:32604",
            HydrofabricNamespace.PUERTO_RICO_NHF: "EPSG:6566",
        }
        return oconus_nhf_crs.get(self, "EPSG:5070")

    @classmethod
    def _missing_(cls, value: object) -> HydrofabricNamespace | None:
        """Handle legacy string values."""
        if not isinstance(value, str):
            return None
        aliases = {
            "nhf": cls.NHF,
            "conus_nhf": cls.CONUS_NHF,
            "ak_nhf": cls.ALASKA_NHF,
            "hi_nhf": cls.HAWAII_NHF,
            "prvi_nhf": cls.PUERTO_RICO_NHF,
            "conus_hf": cls.CONUS_HF,
            "ak_hf": cls.ALASKA_HF,
            "hi_hf": cls.HAWAII_HF,
            "prvi_hf": cls.PUERTO_RICO_HF,
            "gl_hf": cls.GREAT_LAKES_HF,
            "mock_hf": cls.MOCK_HF,
        }
        return aliases.get(value)

    @classmethod
    def resolve(
        cls,
        domain: GeographicDomain | str | None,
        source: HydrofabricSource | str | None,
    ) -> HydrofabricNamespace:
        """Resolve domain/source to namespace.

        Parameters
        ----------
        domain : GeographicDomain | str | None
            The domain to resolve. Can be a GeographicDomain value, a legacy string
            value (nhf, conus_hf, etc.), or a geographic domain string (CONUS, Alaska, etc.).
        source : HydrofabricSource | None
            The hydrofabric source (nhf or hf). Required when using GeographicDomain.

        Returns
        -------
        HydrofabricNamespace
            The resolved namespace.

        Raises
        ------
        ValueError
            If source is provided without domain, or if invalid combination is given.
        NotImplementedError
            If the domain is not available for the requested source (e.g., Alaska with NHF).
        """
        # Neither domain nor source provided - use default
        if domain is None and source is None:
            return cls.NHF

        # Source provided without domain - error
        if source is not None and domain is None:
            raise ValueError("When 'source' is provided, 'domain' must also be specified.")

        # Convert source to HydrofabricSource if it's a string
        if isinstance(source, str):
            try:
                source = HydrofabricSource(source)
            except ValueError:
                raise ValueError(f"Invalid source '{source}'. Valid values are: 'nhf', 'hf'") from None

        # Domain provided without source - legacy mode or default to HF
        if source is None and domain is not None:
            # Check if it's a GeographicDomain instance directly - default to HF
            if isinstance(domain, GeographicDomain):
                source = HydrofabricSource.HF
                # Fall through to the "both provided" case below
            else:
                # Try as a legacy domain value first
                domain_str = str(domain)
                try:
                    return cls(domain_str)
                except ValueError:
                    pass

                # Try as a GeographicDomain string - default to HF
                try:
                    domain = GeographicDomain(domain_str)
                    source = HydrofabricSource.HF
                    # Fall through to the "both provided" case below
                except ValueError:
                    raise ValueError(f"Unknown domain value: '{domain_str}'") from None

        # Both source and domain provided - resolve to namespace
        # Convert domain to GeographicDomain if it's a string
        if isinstance(domain, str):
            # Check if it's a legacy domain string with source provided
            legacy_str_to_geo = {
                "conus_hf": GeographicDomain.CONUS,
                "ak_hf": GeographicDomain.ALASKA,
                "hi_hf": GeographicDomain.HAWAII,
                "prvi_hf": GeographicDomain.PUERTO_RICO,
                "gl_hf": GeographicDomain.GREAT_LAKES,
                "nhf": GeographicDomain.CONUS,
            }
            if domain in legacy_str_to_geo:
                domain = legacy_str_to_geo[domain]
            else:
                try:
                    domain = GeographicDomain(domain)
                except ValueError:
                    raise ValueError(
                        f"Invalid geographic domain '{domain}'. "
                        f"Valid values are: {', '.join(d.value for d in GeographicDomain)}"
                    ) from None

        # Mapping from (GeographicDomain, HydrofabricSource) to namespace
        domain_source_mapping: dict[
            tuple[GeographicDomain, HydrofabricSource], HydrofabricNamespace | None
        ] = {
            (GeographicDomain.CONUS, HydrofabricSource.NHF): cls.CONUS_NHF,
            (GeographicDomain.CONUS, HydrofabricSource.HF): cls.CONUS_HF,
            (GeographicDomain.ALASKA, HydrofabricSource.NHF): cls.ALASKA_NHF,
            (GeographicDomain.ALASKA, HydrofabricSource.HF): cls.ALASKA_HF,
            (GeographicDomain.HAWAII, HydrofabricSource.NHF): cls.HAWAII_NHF,
            (GeographicDomain.HAWAII, HydrofabricSource.HF): cls.HAWAII_HF,
            (GeographicDomain.PUERTO_RICO, HydrofabricSource.NHF): cls.PUERTO_RICO_NHF,
            (GeographicDomain.PUERTO_RICO, HydrofabricSource.HF): cls.PUERTO_RICO_HF,
            (GeographicDomain.GREAT_LAKES, HydrofabricSource.NHF): None,
            (GeographicDomain.GREAT_LAKES, HydrofabricSource.HF): cls.GREAT_LAKES_HF,
        }

        namespace = domain_source_mapping.get((domain, source))  # type: ignore[arg-type]

        if namespace is None:
            raise NotImplementedError(
                f"Domain '{domain.value}' is not currently available for source '{source.value}'."  # type: ignore[union-attr]
            )

        return namespace
