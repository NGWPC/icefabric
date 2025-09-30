import polars as pl
import pytest

from icefabric.modules import (
    get_lasam_parameters,
    get_lstm_parameters,
    get_noahowp_parameters,
    get_sacsma_parameters,
    get_smp_parameters,
    get_snow17_parameters,
    get_topmodel_parameters,
    get_troute_parameters,
)


@pytest.fixture
def test_identifiers(mock_catalog):
    """Fixture that provides test identifiers for parameterization"""
    catalog = mock_catalog("glue")
    domain = "mock_hf"

    # Get identifiers once for all tests
    network_table = catalog.load_table(f"{domain}.network").to_polars()
    identifiers = (
        network_table.select(pl.col("hl_uri"))
        .filter(pl.col("hl_uri").is_not_null())
        .collect()
        .to_pandas()
        .values.squeeze()
    )
    return identifiers


def test_topmodel_parameters(mock_catalog, sample_graph, test_identifiers):
    """Test Topmodel parameter generation and attribute count for all identifiers"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        topmodel_models = get_topmodel_parameters(
            catalog,
            namespace,
            identifier,
            graph=sample_graph,
        )

        assert len(topmodel_models) > 0, f"No Topmodel parameters generated for {identifier}"


def test_noahowp_parameters(mock_catalog, sample_graph, test_identifiers):
    """Test Noah OWP Modular parameter generation and attribute count for all identifiers"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        noahowp_models = get_noahowp_parameters(
            catalog,
            namespace,
            identifier,
            graph=sample_graph,
        )

        assert len(noahowp_models) > 0, f"No Noah OWP parameters generated for {identifier}"


def test_troute_parameters(mock_catalog, sample_graph, test_identifiers):
    """Test T-Route parameter generation and attribute count for all identifiers"""
    mock_catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        troute_models = get_troute_parameters(
            mock_catalog,
            namespace,
            identifier,
            graph=sample_graph,
        )

        assert len(troute_models) > 0, f"No T-Route parameters generated for {identifier}"


@pytest.mark.parametrize("sft_included", [False, True])
def test_lasam_parameters(mock_catalog, sample_graph, test_identifiers, sft_included):
    """Test LASAM parameter generation with different sft_included values"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        lasam_models = get_lasam_parameters(
            catalog,
            namespace,
            identifier,
            sft_included=sft_included,
            soil_params_file="vG_default_params_HYDRUS.dat",
            graph=sample_graph,
        )

        assert len(lasam_models) > 0, f"No LASAM parameters generated for {identifier}"


@pytest.mark.parametrize("envca", [True, False])
def test_snow17_parameters(mock_catalog, sample_graph, test_identifiers, envca):
    """Test Snow17 parameter generation with different envca values"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        snow17_models = get_snow17_parameters(
            catalog,
            namespace,
            identifier,
            envca=envca,
            graph=sample_graph,
        )

        assert len(snow17_models) > 0, f"No Snow17 parameters generated for {identifier}"


@pytest.mark.parametrize("envca", [True, False])
def test_sacsma_parameters(mock_catalog, sample_graph, test_identifiers, envca):
    """Test SAC-SMA parameter generation with different envca values"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        sacsma_models = get_sacsma_parameters(catalog, namespace, identifier, envca=envca, graph=sample_graph)

        assert len(sacsma_models) > 0, f"No SAC-SMA parameters generated for {identifier}"


@pytest.mark.parametrize("module_type", ["TopModel", "CFE-S", "CFE-X", "LASAM"])
def test_smp_parameters(mock_catalog, sample_graph, test_identifiers, module_type):
    """Test SMP parameter generation for different modules"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        smp_models = get_smp_parameters(
            catalog,
            namespace,
            identifier,
            module=module_type,
            graph=sample_graph,
        )

        assert len(smp_models) > 0, f"No SMP parameters generated for {identifier} with {module_type}"


def test_lstm_parameters(mock_catalog, sample_graph, test_identifiers):
    """Test LSTM parameter generation and attribute count for all identifiers"""
    catalog = mock_catalog("glue")
    namespace = "mock_hf"
    for identifier in test_identifiers:
        lstm_models = get_lstm_parameters(
            catalog,
            namespace,
            identifier,
            graph=sample_graph,
        )

        assert len(lstm_models) > 0, f"No LSTM parameters generated for {identifier}"
