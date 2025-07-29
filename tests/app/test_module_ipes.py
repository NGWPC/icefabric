from icefabric.modules import *
from pyiceberg.catalog import load_catalog
from icefabric.schemas.hydrofabric import HydrofabricDomains

def test_module_ipes():
    """Test in verifying number of attributes of a given module"""
    catalog = load_catalog("glue", **{"type": "glue", "glue.region": "us-east-1"})
    domain = HydrofabricDomains.CONUS
    identifier = '06710385'

    # Topmodel
    topmodel_pydantic_models = get_topmodel_parameters(catalog,
                                                       domain,
                                                       identifier)
    # Noah OWP
    noahowp_pydantic_models = get_noahowp_parameters(catalog,
                                                     domain,
                                                     identifier)

    # T-Route
    troute_pydantic_models = get_troute_parameters(catalog,
                                                   domain,
                                                   identifier)

    # LASAM
    lasam_pydantic_models0 = get_lasam_parameters(catalog,
                                                 domain,
                                                 identifier,
                                                 sft_included=False,
                                                 soil_params_file="vG_default_params_HYDRUS.dat")
    lasam_pydantic_models1 = get_lasam_parameters(catalog,
                                                 domain,
                                                 identifier,
                                                 sft_included=True,
                                                 soil_params_file="vG_default_params_HYDRUS.dat")

    # Snow17
    snow17_pydantic_models0 = get_snow17_parameters(catalog,
                                                    domain,
                                                    identifier,
                                                    conus_only=False,
                                                    envca=True)
    snow17_pydantic_models1 = get_snow17_parameters(catalog,
                                                    domain,
                                                    identifier,
                                                    conus_only=True,
                                                    envca=False)

    # SAC SMA
    sacsma_pydantic_models0 = get_sacsma_parameters(catalog,
                                                    domain,
                                                    identifier,
                                                    conus_only=True,
                                                    envca=False)
    sacsma_pydantic_models1 = get_sacsma_parameters(catalog,
                                                    domain,
                                                    identifier,
                                                    conus_only=True,
                                                    envca=True)

    # SMP
    smp_pydantic_models = get_smp_parameters(catalog,
                                             domain,
                                             identifier,
                                             'TopModel')

    # LSTM
    lstm_pydantic_models = get_lstm_parameters(catalog,
                                               domain,
                                               identifier)
    
    for i in range(1):
        tm_variables = [attr for attr in dir(topmodel_pydantic_models[i]) if not attr.startswith('__')]
        assert len(tm_variables) == 59, "Incorrect Number of Attributes For Topmodel"
        
        noah_variables = [attr for attr in dir(noahowp_pydantic_models[i]) if not attr.startswith('__')]
        assert len(noah_variables) == 83, "Incorrect Number of Attributes For Noah OWP Modular"

        troute_variables = [attr for attr in dir(troute_pydantic_models[i]) if not attr.startswith('__')]
        assert len(troute_variables) == 46, "Incorrect Number of Attributes For T-Route"

        lasam_variables0 = [attr for attr in dir(lasam_pydantic_models0[i]) if not attr.startswith('__')]
        assert len(lasam_variables0) == 55, "Incorrect Number of Attributes For LASAM (w/ sft_included=False)"
        
        lasam_variables1 = [attr for attr in dir(lasam_pydantic_models1[i]) if not attr.startswith('__')]
        assert len(lasam_variables1) == 55, "Incorrect Number of Attributes For LASAM (w/ sft_included=True)"

        snow17_variables0 = [attr for attr in dir(snow17_pydantic_models0[i]) if not attr.startswith('__')]
        assert len(snow17_variables0) == 63, "Incorrect Number of Attributes For Snow17 (w/ conus_only=False, envca=True)"

        snow17_variables1 = [attr for attr in dir(snow17_pydantic_models1[i]) if not attr.startswith('__')]
        assert len(snow17_variables1) == 63, "Incorrect Number of Attributes For Snow17 (w/ conus_only=True, envca=False)"

        sacsma_variables0 = [attr for attr in dir(sacsma_pydantic_models0[i]) if not attr.startswith('__')]
        assert len(sacsma_variables0) == 55, "Incorrect Number of Attributes For SACSMA (w/ conus_only=True, envca=False)"

        sacsma_variables1 = [attr for attr in dir(sacsma_pydantic_models1[i]) if not attr.startswith('__')]
        assert len(sacsma_variables1) == 55, "Incorrect Number of Attributes For SACSMA (w/ conus_only=True, envca=True)"

        smp_variables = [attr for attr in dir(smp_pydantic_models[i]) if not attr.startswith('__')]
        assert len(smp_variables) == 49, "Incorrect Number of Attributes For SMP (w/ module='TopModel')"

        lstm_variables = [attr for attr in dir(lstm_pydantic_models[i]) if not attr.startswith('__')]
        assert len(lstm_variables) == 48, "Incorrect Number of Attributes For LSTM"
        
