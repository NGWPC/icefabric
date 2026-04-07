"""Tests for the source query parameter functionality."""

import pytest

from icefabric.schemas.hydrofabric import (
    GeographicDomain,
    HydrofabricNamespace,
    HydrofabricSource,
)


class TestHydrofabricNamespaceResolve:
    """Unit tests for the HydrofabricNamespace.resolve method."""

    def test_default_no_params(self):
        """Test that no params returns NHF with is_nhf=True."""
        namespace = HydrofabricNamespace.resolve(None, None)
        assert namespace == "nhf"
        assert namespace.is_nhf is True

    def test_source_without_domain_raises(self):
        """Test that providing source without domain raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            HydrofabricNamespace.resolve(None, HydrofabricSource.NHF)
        assert "domain" in str(exc_info.value).lower()

    def test_geographic_domain_without_source_defaults_to_hf(self):
        """Test that providing GeographicDomain without source defaults to HF."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.CONUS, None)
        assert namespace == "conus_hf"
        assert namespace.is_nhf is False

    def test_geographic_domain_alaska_without_source_defaults_to_hf(self):
        """Test that Alaska without source defaults to HF (ak_hf)."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.ALASKA, None)
        assert namespace == "ak_hf"
        assert namespace.is_nhf is False

    def test_geographic_domain_hawaii_without_source_defaults_to_hf(self):
        """Test that Hawaii without source defaults to HF (hi_hf)."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.HAWAII, None)
        assert namespace == "hi_hf"
        assert namespace.is_nhf is False

    def test_geographic_domain_puerto_rico_without_source_defaults_to_hf(self):
        """Test that Puerto_Rico without source defaults to HF (prvi_hf)."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.PUERTO_RICO, None)
        assert namespace == "prvi_hf"
        assert namespace.is_nhf is False

    def test_geographic_domain_great_lakes_without_source_defaults_to_hf(self):
        """Test that Great_Lakes without source defaults to HF (gl_hf)."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.GREAT_LAKES, None)
        assert namespace == "gl_hf"
        assert namespace.is_nhf is False

    def test_string_geographic_domain_without_source_defaults_to_hf(self):
        """Test that string geographic domain without source defaults to HF."""
        namespace = HydrofabricNamespace.resolve("CONUS", None)
        assert namespace == "conus_hf"
        assert namespace.is_nhf is False

    def test_string_geographic_domain_hawaii_without_source_defaults_to_hf(self):
        """Test that string 'Hawaii' without source defaults to HF."""
        namespace = HydrofabricNamespace.resolve("Hawaii", None)
        assert namespace == "hi_hf"
        assert namespace.is_nhf is False

    # Legacy domain tests - backwards compatibility (using string values)
    def test_legacy_domain_nhf(self):
        """Test legacy 'nhf' domain returns NHF namespace."""
        namespace = HydrofabricNamespace.resolve("nhf", None)
        assert namespace == "nhf"
        assert namespace.is_nhf is True

    def test_legacy_domain_conus_hf(self):
        """Test legacy 'conus_hf' domain returns conus_hf namespace."""
        namespace = HydrofabricNamespace.resolve("conus_hf", None)
        assert namespace == "conus_hf"
        assert namespace.is_nhf is False

    def test_legacy_domain_ak_hf(self):
        """Test legacy 'ak_hf' domain returns ak_hf namespace."""
        namespace = HydrofabricNamespace.resolve("ak_hf", None)
        assert namespace == "ak_hf"
        assert namespace.is_nhf is False

    def test_legacy_domain_hi_hf(self):
        """Test legacy 'hi_hf' domain returns hi_hf namespace."""
        namespace = HydrofabricNamespace.resolve("hi_hf", None)
        assert namespace == "hi_hf"
        assert namespace.is_nhf is False

    def test_legacy_domain_prvi_hf(self):
        """Test legacy 'prvi_hf' domain returns prvi_hf namespace."""
        namespace = HydrofabricNamespace.resolve("prvi_hf", None)
        assert namespace == "prvi_hf"
        assert namespace.is_nhf is False

    def test_legacy_domain_gl_hf(self):
        """Test legacy 'gl_hf' domain returns gl_hf namespace."""
        namespace = HydrofabricNamespace.resolve("gl_hf", None)
        assert namespace == "gl_hf"
        assert namespace.is_nhf is False

    # New API tests - source + domain combinations
    def test_conus_nhf(self):
        """Test CONUS + NHF returns conus_nhf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.CONUS, HydrofabricSource.NHF)
        assert namespace == "conus_nhf"
        assert namespace.is_nhf is True

    def test_conus_hf(self):
        """Test CONUS + HF returns conus_hf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.CONUS, HydrofabricSource.HF)
        assert namespace == "conus_hf"
        assert namespace.is_nhf is False

    def test_alaska_hf(self):
        """Test Alaska + HF returns ak_hf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.ALASKA, HydrofabricSource.HF)
        assert namespace == "ak_hf"
        assert namespace.is_nhf is False

    def test_hawaii_hf(self):
        """Test Hawaii + HF returns hi_hf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.HAWAII, HydrofabricSource.HF)
        assert namespace == "hi_hf"
        assert namespace.is_nhf is False

    def test_puerto_rico_hf(self):
        """Test Puerto_Rico + HF returns prvi_hf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.PUERTO_RICO, HydrofabricSource.HF)
        assert namespace == "prvi_hf"
        assert namespace.is_nhf is False

    def test_great_lakes_hf(self):
        """Test Great_Lakes + HF returns gl_hf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.GREAT_LAKES, HydrofabricSource.HF)
        assert namespace == "gl_hf"
        assert namespace.is_nhf is False

    # Non-CONUS NHF domain tests
    def test_alaska_nhf(self):
        """Test Alaska + NHF returns ak_nhf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.ALASKA, HydrofabricSource.NHF)
        assert namespace == "ak_nhf"
        assert namespace.is_nhf is True

    def test_hawaii_nhf(self):
        """Test Hawaii + NHF returns hi_nhf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.HAWAII, HydrofabricSource.NHF)
        assert namespace == "hi_nhf"
        assert namespace.is_nhf is True

    def test_puerto_rico_nhf(self):
        """Test Puerto_Rico + NHF returns prvi_nhf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.PUERTO_RICO, HydrofabricSource.NHF)
        assert namespace == "prvi_nhf"
        assert namespace.is_nhf is True

    def test_great_lakes_nhf_not_implemented(self):
        """Test Great_Lakes + NHF raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            HydrofabricNamespace.resolve(GeographicDomain.GREAT_LAKES, HydrofabricSource.NHF)

    # String input tests
    def test_string_domain_conus(self):
        """Test string domain 'CONUS' with source."""
        namespace = HydrofabricNamespace.resolve("CONUS", HydrofabricSource.HF)
        assert namespace == "conus_hf"
        assert namespace.is_nhf is False

    def test_string_source_nhf(self):
        """Test string source 'nhf' with domain returns conus_nhf namespace."""
        namespace = HydrofabricNamespace.resolve(GeographicDomain.CONUS, "nhf")
        assert namespace == "conus_nhf"
        assert namespace.is_nhf is True

    def test_invalid_string_domain(self):
        """Test invalid string domain raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            HydrofabricNamespace.resolve("InvalidDomain", HydrofabricSource.HF)
        assert "Invalid" in str(exc_info.value)

    def test_invalid_string_source(self):
        """Test invalid string source raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            HydrofabricNamespace.resolve(GeographicDomain.CONUS, "invalid")
        assert "Invalid" in str(exc_info.value)


class TestHydrofabricNamespaceProperties:
    """Test HydrofabricNamespace enum properties."""

    def test_is_nhf_for_nhf(self):
        """Test is_nhf returns True for NHF namespace."""
        assert HydrofabricNamespace.NHF.is_nhf is True

    def test_is_nhf_for_conus_nhf(self):
        """Test is_nhf returns True for CONUS_NHF namespace."""
        assert HydrofabricNamespace.CONUS_NHF.is_nhf is True

    def test_is_nhf_for_alaska_nhf(self):
        """Test is_nhf returns True for ALASKA_NHF namespace."""
        assert HydrofabricNamespace.ALASKA_NHF.is_nhf is True

    def test_is_nhf_for_hawaii_nhf(self):
        """Test is_nhf returns True for HAWAII_NHF namespace."""
        assert HydrofabricNamespace.HAWAII_NHF.is_nhf is True

    def test_is_nhf_for_puerto_rico_nhf(self):
        """Test is_nhf returns True for PUERTO_RICO_NHF namespace."""
        assert HydrofabricNamespace.PUERTO_RICO_NHF.is_nhf is True

    def test_is_nhf_for_conus_hf(self):
        """Test is_nhf returns False for CONUS_HF namespace."""
        assert HydrofabricNamespace.CONUS_HF.is_nhf is False

    def test_is_oconus_hf_for_alaska(self):
        """Test is_oconus_hf returns True for ALASKA_HF namespace."""
        assert HydrofabricNamespace.ALASKA_HF.is_oconus_hf is True

    def test_is_oconus_hf_for_conus(self):
        """Test is_oconus_hf returns False for CONUS_HF namespace."""
        assert HydrofabricNamespace.CONUS_HF.is_oconus_hf is False

    def test_is_oconus_hf_for_hawaii(self):
        """Test is_oconus_hf returns False for HAWAII_HF namespace (it's OCONUS but not in the set)."""
        assert HydrofabricNamespace.HAWAII_HF.is_oconus_hf is False

    def test_crs_for_conus_nhf(self):
        """CONUS NHF is stored in EPSG:5070 (NAD83 / Conus Albers)."""
        assert HydrofabricNamespace.NHF.crs == "EPSG:5070"
        assert HydrofabricNamespace.CONUS_NHF.crs == "EPSG:5070"

    def test_crs_for_alaska_nhf(self):
        """Alaska NHF is stored in EPSG:3338 (NAD83 / Alaska Albers)."""
        assert HydrofabricNamespace.ALASKA_NHF.crs == "EPSG:3338"

    def test_crs_for_hawaii_nhf(self):
        """Hawaii NHF is stored in EPSG:32604 (WGS 84 / UTM 4N)."""
        assert HydrofabricNamespace.HAWAII_NHF.crs == "EPSG:32604"

    def test_crs_for_puerto_rico_nhf(self):
        """Puerto Rico / USVI NHF is stored in EPSG:6566."""
        assert HydrofabricNamespace.PUERTO_RICO_NHF.crs == "EPSG:6566"


class TestHydrofabricRouterSourceParameter:
    """Integration tests for the hydrofabric router source parameter."""

    @pytest.mark.slow
    def test_hydrofabric_legacy_domain_hi_hf(self, client, watershed_bound_id_good: str):
        """Test hydrofabric endpoint with legacy hi_hf domain still works."""
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=flowpath_id&domain=hi_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200

    @pytest.mark.slow
    def test_hydrofabric_new_api_hawaii_hf(self, client, watershed_bound_id_good: str):
        """Test hydrofabric endpoint with new source=hf&domain=Hawaii.

        Note: The mock uses hi_hf namespace which maps to Hawaii domain.
        """
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=flowpath_id&source=hf&domain=Hawaii&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200

    def test_hydrofabric_great_lakes_nhf_returns_501(self, client):
        """Test hydrofabric endpoint returns 501 for Great Lakes with NHF."""
        response = client.get(
            "/v1/hydrofabric/test-id/gpkg?id_type=flowpath_id&source=nhf&domain=Great_Lakes&layers=divides"
        )
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"

    def test_hydrofabric_source_without_domain_returns_400(self, client):
        """Test hydrofabric endpoint returns 400 when source provided without domain."""
        response = client.get("/v1/hydrofabric/test-id/gpkg?id_type=flowpath_id&source=nhf")
        assert response.status_code == 400

    @pytest.mark.slow
    def test_hydrofabric_geographic_domain_without_source_succeeds(
        self, client, watershed_bound_id_good: str
    ):
        """Test hydrofabric endpoint works with just domain=Hawaii (no source).

        Should default to HF source and return hi_hf data.
        """
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=flowpath_id&domain=Hawaii&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200


class TestModuleRouterSourceParameter:
    """Integration tests for the NWM module routers source parameter."""

    def test_module_sft_great_lakes_nhf_returns_501(self, client):
        """Test SFT endpoint returns 501 for Great Lakes with NHF."""
        response = client.get("/v1/modules/sft/?identifier=01010000&source=nhf&domain=Great_Lakes")
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"

    def test_module_sft_source_without_domain_returns_400(self, client):
        """Test SFT endpoint returns 400 when source provided without domain."""
        response = client.get("/v1/modules/sft/?identifier=01010000&source=nhf")
        assert response.status_code == 400

    def test_module_parameter_metadata_great_lakes_nhf_returns_501(self, client):
        """Test parameter_metadata endpoint returns 501 for Great Lakes with NHF."""
        response = client.get(
            "/v1/modules/parameter_metadata/?modules=SFT&source=nhf&domain=Great_Lakes&gage_id=01010000"
        )
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"
