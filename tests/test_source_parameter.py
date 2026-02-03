"""Tests for the source query parameter functionality."""

import pytest

from icefabric.schemas.hydrofabric import (
    GeographicDomain,
    HydrofabricDomains,
    HydrofabricSource,
    resolve_namespace,
)


class TestResolveNamespace:
    """Unit tests for the resolve_namespace function."""

    def test_default_no_params(self):
        """Test that no params returns NHF with is_nhf=True."""
        namespace, is_nhf, warnings = resolve_namespace(None, None)
        assert namespace == "nhf"
        assert is_nhf is True
        assert warnings == []

    def test_source_without_domain_raises(self):
        """Test that providing source without domain raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            resolve_namespace(None, HydrofabricSource.NHF)
        assert "domain" in str(exc_info.value).lower()

    def test_geographic_domain_without_source_defaults_to_hf(self):
        """Test that providing GeographicDomain without source defaults to HF."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.CONUS, None)
        assert namespace == "conus_hf"
        assert is_nhf is False
        assert warnings == []

    def test_geographic_domain_alaska_without_source_defaults_to_hf(self):
        """Test that Alaska without source defaults to HF (ak_hf)."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.ALASKA, None)
        assert namespace == "ak_hf"
        assert is_nhf is False
        assert warnings == []

    def test_geographic_domain_hawaii_without_source_defaults_to_hf(self):
        """Test that Hawaii without source defaults to HF (hi_hf)."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.HAWAII, None)
        assert namespace == "hi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_geographic_domain_puerto_rico_without_source_defaults_to_hf(self):
        """Test that Puerto_Rico without source defaults to HF (prvi_hf)."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.PUERTO_RICO, None)
        assert namespace == "prvi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_geographic_domain_great_lakes_without_source_defaults_to_hf(self):
        """Test that Great_Lakes without source defaults to HF (gl_hf)."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.GREAT_LAKES, None)
        assert namespace == "gl_hf"
        assert is_nhf is False
        assert warnings == []

    def test_string_geographic_domain_without_source_defaults_to_hf(self):
        """Test that string geographic domain without source defaults to HF."""
        namespace, is_nhf, warnings = resolve_namespace("CONUS", None)
        assert namespace == "conus_hf"
        assert is_nhf is False
        assert warnings == []

    def test_string_geographic_domain_hawaii_without_source_defaults_to_hf(self):
        """Test that string 'Hawaii' without source defaults to HF."""
        namespace, is_nhf, warnings = resolve_namespace("Hawaii", None)
        assert namespace == "hi_hf"
        assert is_nhf is False
        assert warnings == []

    # Legacy domain tests - backwards compatibility
    def test_legacy_domain_nhf(self):
        """Test legacy 'nhf' domain returns NHF namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.NHF, None)
        assert namespace == "nhf"
        assert is_nhf is True
        assert warnings == []

    def test_legacy_domain_conus_hf(self):
        """Test legacy 'conus_hf' domain returns conus_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.CONUS, None)
        assert namespace == "conus_hf"
        assert is_nhf is False
        assert warnings == []

    def test_legacy_domain_ak_hf(self):
        """Test legacy 'ak_hf' domain returns ak_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.AK, None)
        assert namespace == "ak_hf"
        assert is_nhf is False
        assert warnings == []

    def test_legacy_domain_hi_hf(self):
        """Test legacy 'hi_hf' domain returns hi_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.HI, None)
        assert namespace == "hi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_legacy_domain_prvi_hf(self):
        """Test legacy 'prvi_hf' domain returns prvi_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.PRVI, None)
        assert namespace == "prvi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_legacy_domain_gl_hf(self):
        """Test legacy 'gl_hf' domain returns gl_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(HydrofabricDomains.GL, None)
        assert namespace == "gl_hf"
        assert is_nhf is False
        assert warnings == []

    # New API tests - source + domain combinations
    def test_conus_nhf(self):
        """Test CONUS + NHF returns nhf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.CONUS, HydrofabricSource.NHF)
        assert namespace == "nhf"
        assert is_nhf is True
        assert warnings == []

    def test_conus_hf(self):
        """Test CONUS + HF returns conus_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.CONUS, HydrofabricSource.HF)
        assert namespace == "conus_hf"
        assert is_nhf is False
        assert warnings == []

    def test_alaska_hf(self):
        """Test Alaska + HF returns ak_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.ALASKA, HydrofabricSource.HF)
        assert namespace == "ak_hf"
        assert is_nhf is False
        assert warnings == []

    def test_hawaii_hf(self):
        """Test Hawaii + HF returns hi_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.HAWAII, HydrofabricSource.HF)
        assert namespace == "hi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_puerto_rico_hf(self):
        """Test Puerto_Rico + HF returns prvi_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.PUERTO_RICO, HydrofabricSource.HF)
        assert namespace == "prvi_hf"
        assert is_nhf is False
        assert warnings == []

    def test_great_lakes_hf(self):
        """Test Great_Lakes + HF returns gl_hf namespace."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.GREAT_LAKES, HydrofabricSource.HF)
        assert namespace == "gl_hf"
        assert is_nhf is False
        assert warnings == []

    # 501 Not Implemented tests - non-CONUS with NHF
    def test_alaska_nhf_not_implemented(self):
        """Test Alaska + NHF raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            resolve_namespace(GeographicDomain.ALASKA, HydrofabricSource.NHF)
        assert "Alaska" in str(exc_info.value)
        assert "CONUS" in str(exc_info.value)

    def test_hawaii_nhf_not_implemented(self):
        """Test Hawaii + NHF raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            resolve_namespace(GeographicDomain.HAWAII, HydrofabricSource.NHF)
        assert "Hawaii" in str(exc_info.value)
        assert "CONUS" in str(exc_info.value)

    def test_puerto_rico_nhf_not_implemented(self):
        """Test Puerto_Rico + NHF raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            resolve_namespace(GeographicDomain.PUERTO_RICO, HydrofabricSource.NHF)
        assert "Puerto_Rico" in str(exc_info.value)
        assert "CONUS" in str(exc_info.value)

    def test_great_lakes_nhf_not_implemented(self):
        """Test Great_Lakes + NHF raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            resolve_namespace(GeographicDomain.GREAT_LAKES, HydrofabricSource.NHF)
        assert "Great_Lakes" in str(exc_info.value)
        assert "CONUS" in str(exc_info.value)

    # String input tests
    def test_string_domain_conus(self):
        """Test string domain 'CONUS' with source."""
        namespace, is_nhf, warnings = resolve_namespace("CONUS", HydrofabricSource.HF)
        assert namespace == "conus_hf"
        assert is_nhf is False

    def test_string_source_nhf(self):
        """Test string source 'nhf' with domain."""
        namespace, is_nhf, warnings = resolve_namespace(GeographicDomain.CONUS, "nhf")
        assert namespace == "nhf"
        assert is_nhf is True

    def test_invalid_string_domain(self):
        """Test invalid string domain raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            resolve_namespace("InvalidDomain", HydrofabricSource.HF)
        assert "Invalid" in str(exc_info.value)

    def test_invalid_string_source(self):
        """Test invalid string source raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            resolve_namespace(GeographicDomain.CONUS, "invalid")
        assert "Invalid" in str(exc_info.value)


class TestHydrofabricRouterSourceParameter:
    """Integration tests for the hydrofabric router source parameter."""

    @pytest.mark.slow
    def test_hydrofabric_legacy_domain_hi_hf(self, client, watershed_bound_id_good: str):
        """Test hydrofabric endpoint with legacy hi_hf domain still works."""
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=id&domain=hi_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200

    @pytest.mark.slow
    def test_hydrofabric_new_api_hawaii_hf(self, client, watershed_bound_id_good: str):
        """Test hydrofabric endpoint with new source=hf&domain=Hawaii.

        Note: The mock uses hi_hf namespace which maps to Hawaii domain.
        """
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=id&source=hf&domain=Hawaii&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200

    def test_hydrofabric_non_conus_nhf_returns_501(self, client):
        """Test hydrofabric endpoint returns 501 for non-CONUS domains with NHF."""
        response = client.get("/v1/hydrofabric/test-id/gpkg?id_type=id&source=nhf&domain=Hawaii&layers=divides")
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"
        assert "CONUS" in data["detail"]["available_domains"]

    def test_hydrofabric_source_without_domain_returns_400(self, client):
        """Test hydrofabric endpoint returns 400 when source provided without domain."""
        response = client.get("/v1/hydrofabric/test-id/gpkg?id_type=id&source=nhf")
        assert response.status_code == 400

    @pytest.mark.slow
    def test_hydrofabric_geographic_domain_without_source_succeeds(self, client, watershed_bound_id_good: str):
        """Test hydrofabric endpoint works with just domain=Hawaii (no source).

        Should default to HF source and return hi_hf data.
        """
        response = client.get(
            f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg"
            "?id_type=id&domain=Hawaii&layers=divides&layers=flowpaths&layers=network&layers=nexus"
        )
        assert response.status_code == 200


class TestModuleRouterSourceParameter:
    """Integration tests for the NWM module routers source parameter."""

    def test_module_sft_non_conus_nhf_returns_501(self, client):
        """Test SFT endpoint returns 501 for non-CONUS domains with NHF."""
        response = client.get("/v1/modules/sft/?identifier=01010000&source=nhf&domain=Alaska")
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"

    def test_module_sft_source_without_domain_returns_400(self, client):
        """Test SFT endpoint returns 400 when source provided without domain."""
        response = client.get("/v1/modules/sft/?identifier=01010000&source=nhf")
        assert response.status_code == 400

    def test_module_parameter_metadata_non_conus_nhf_returns_501(self, client):
        """Test parameter_metadata endpoint returns 501 for non-CONUS domains with NHF."""
        response = client.get("/v1/modules/parameter_metadata/?modules=SFT&source=nhf&domain=Alaska&gage_id=01010000")
        assert response.status_code == 501
        data = response.json()
        assert data["detail"]["error"] == "domain_not_available"
