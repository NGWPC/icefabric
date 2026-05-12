import enum


class DivideAttributesHF(enum.Enum):
    """Enum containing Hydrofabric 2.2 divide attribute names"""

    DIVIDE_ID = "divide_id"
    AREA = "areasqkm"
    BEXP = "mode.bexp_soil_layers_stag=1"
    ISLTYP = "mode.ISLTYP"
    IVGTYP = "mode.IVGTYP"
    DKSAT = "geom_mean.dksat_soil_layers_stag=1"
    PSISAT = "geom_mean.psisat_soil_layers_stag=1"
    CWPVT = "mean.cwpvt"
    MFSNO = "mean.mfsno"
    MP = "mean.mp"
    REFKDT = "mean.refkdt"
    SLOPE_1KM = "mean.slope_1km"
    SMCMAX = "mean.smcmax_soil_layers_stag=1"
    SMCWLT = "mean.smcwlt_soil_layers_stag=1"
    VCMX25 = "mean.vcmx25"
    COEFF = "mean.Coeff"
    ZMAX = "mean.Zmax"
    EXPON = "mode.Expon"
    X = "centroid_x"
    Y = "centroid_y"
    IMPERVIOUS = "mean.impervious"
    ELEVATION = "mean.elevation"
    SLOPE = "mean.slope"
    ASPECT = "circ_mean.aspect"
    TWI = "dist_4.twi"
    FLOWPATH_LENGTH = "lengthkm"
    GLACIER_PERCENT = "glacier_percent"
    AXAJ = "a_Xinanjiang_inflection_point_parameter"
    BXAJ = "b_Xinanjiang_shape_parameter"
    XXAJ = "x_Xinanjiang_shape_parameter"
    LZFPM = "lzfpm"
    LZPK = "lzpk"
    LZTWM = "lztwm"
    REXP = "rexp"
    UZK = "uzk"
    ZPERC = "zperc"
    LZFSM = "lzfsm"
    LZSK = "lzsk"
    PFREE = "pfree"
    UZFWM = "uzfwm"
    UZTWM = "uztwm"
    MFMIN = "mfmin"
    MFMAX = "mfmax"
    UADJ = "uadj"
    JAN = "jan_temp_range"
    FEB = "feb_temp_range"
    MAR = "mar_temp_range"
    APR = "apr_temp_range"
    MAY = "may_temp_range"
    JUN = "jun_temp_range"
    JUL = "jul_temp_range"
    AUG = "aug_temp_range"
    SEP = "sep_temp_range"
    OCT = "oct_temp_range"
    NOV = "nov_temp_range"
    DEC = "dec_temp_range"


class DivideAttributesNHF(enum.Enum):
    """Enum containing NHF divide attribute names"""

    DIVIDE_ID = "div_id"
    AREA = "area_sqkm"
    BEXP = "bexp_mode"
    ISLTYP = "isltyp_mode"
    IVGTYP = "ivgtyp_mode"
    DKSAT = "dksat_geomean"
    PSISAT = "psisat_geomean"
    CWPVT = "cwpvt_mean"
    MFSNO = "mfsno_mean"
    MP = "mp_mean"
    REFKDT = "refkdt_mean"
    SLOPE_1KM = "slope1km_mean"
    SMCMAX = "smcmax_mean"
    SMCWLT = "smcwlt_mean"
    VCMX25 = "vcmx_mean"
    COEFF = "cgw"
    ZMAX = "max_gw_storage"
    EXPON = "expon"
    TWI_Q25 = "twi_q25"
    TWI_Q50 = "twi_q50"
    TWI_Q75 = "twi_q75"
    TWI_Q100 = "twi_q100"
    X = "lon"
    Y = "lat"
    IMPERVIOUS = "imperv_mean"
    ELEVATION = "elevation_mean"
    SLOPE = "slope250m_mean"
    ASPECT = "aspect_circmean"
    FLOWPATH_LENGTH = "length_km"
    GLACIER_PERCENT = "glacier_percent"
    AXAJ = "a_xinanjiang_inflection_point_parameter"
    BXAJ = "b_xinanjiang_shape_parameter"
    XXAJ = "x_xinanjiang_shape_parameter"
    LZFPM = "lzfpm_mean"
    LZPK = "lzpk_mean"
    LZTWM = "lztwm_mean"
    REXP = "rexp_mean"
    UZK = "uzk_mean"
    ZPERC = "zperc_mean"
    LZFSM = "lzfsm_mean"
    LZSK = "lzsk_mean"
    PFREE = "pfree_mean"
    UZFWM = "uzfwm_mean"
    UZTWM = "uztwm_mean"
    MFMIN = "mfmin_mean"
    MFMAX = "mfmax_mean"
    UADJ = "uadj_mean"
    JAN = "temp_delta_jan_mean"
    FEB = "temp_delta_feb_mean"
    MAR = "temp_delta_mar_mean"
    APR = "temp_delta_apr_mean"
    MAY = "temp_delta_may_mean"
    JUN = "temp_delta_jun_mean"
    JUL = "temp_delta_jul_mean"
    AUG = "temp_delta_aug_mean"
    SEP = "temp_delta_sep_mean"
    OCT = "temp_delta_oct_mean"
    NOV = "temp_delta_nov_mean"
    DEC = "temp_delta_dec_mean"
    QUARTZ = "quartz_mean"
    THETA_R = "theta_r"
    THETA_E = "theta_e"
    ALPHA = "alpha"
    N = "n"
    KS = "Ks"


class ParametersToDivideAttributesNHF:
    """Mapping of parameter names to NHF divide attribute names"""

    parametersNHF = {
        "a_Xinanjiang_inflection_point_parameter": DivideAttributesNHF.AXAJ.value,
        "b_Xinanjiang_shape_parameter": DivideAttributesNHF.BXAJ.value,
        "x_Xinanjiang_shape_parameter": DivideAttributesNHF.XXAJ.value,
        "lzfpm": DivideAttributesNHF.LZFPM.value,
        "lzpk": DivideAttributesNHF.LZPK.value,
        "lztwm": DivideAttributesNHF.LZTWM.value,
        "rexp": DivideAttributesNHF.REXP.value,
        "uzk": DivideAttributesNHF.UZK.value,
        "zperc": DivideAttributesNHF.ZPERC.value,
        "lzfsm": DivideAttributesNHF.LZFSM.value,
        "lzsk": DivideAttributesNHF.LZSK.value,
        "pfree": DivideAttributesNHF.PFREE.value,
        "uzfwm": DivideAttributesNHF.UZFWM.value,
        "uztwm": DivideAttributesNHF.UZTWM.value,
        "mfmin": DivideAttributesNHF.MFMIN.value,
        "mfmax": DivideAttributesNHF.MFMAX.value,
        "uadj": DivideAttributesNHF.UADJ.value,
        "soil_params.b": DivideAttributesNHF.BEXP.value,
        "soil_params.satdk": DivideAttributesNHF.DKSAT.value,
        "soil_params.satpsi": DivideAttributesNHF.PSISAT.value,
        "soil_params.slop": DivideAttributesNHF.SLOPE_1KM.value,
        "soil_params.smcmax": DivideAttributesNHF.SMCMAX.value,
        "soil_params.wltsmc": DivideAttributesNHF.SMCWLT.value,
        "max_gw_storage": DivideAttributesNHF.ZMAX.value,
        "Cgw": DivideAttributesNHF.COEFF.value,
        "expon": DivideAttributesNHF.EXPON.value,
        "theta_r": DivideAttributesNHF.THETA_R.value,
        "theta_e": DivideAttributesNHF.THETA_E.value,
        "alpha": DivideAttributesNHF.ALPHA.value,
        "n": DivideAttributesNHF.N.value,
        "Ks": DivideAttributesNHF.KS.value,
    }


class ParametersToDivideAttributesHF:
    """Mapping of parameter names to 2.2 divide attribute names"""

    parametersHF = {
        "a_Xinanjiang_inflection_point_parameter": DivideAttributesHF.AXAJ.value,
        "b_Xinanjiang_shape_parameter": DivideAttributesHF.BXAJ.value,
        "x_Xinanjiang_shape_parameter": DivideAttributesHF.XXAJ.value,
        "lzfpm": DivideAttributesHF.LZFPM.value,
        "lzpk": DivideAttributesHF.LZPK.value,
        "lztwm": DivideAttributesHF.LZTWM.value,
        "rexp": DivideAttributesHF.REXP.value,
        "uzk": DivideAttributesHF.UZK.value,
        "zperc": DivideAttributesHF.ZPERC.value,
        "lzfsm": DivideAttributesHF.LZFSM.value,
        "lzsk": DivideAttributesHF.LZSK.value,
        "pfree": DivideAttributesHF.PFREE.value,
        "uzfwm": DivideAttributesHF.UZFWM.value,
        "uztwm": DivideAttributesHF.UZTWM.value,
        "mfmin": DivideAttributesHF.MFMIN.value,
        "mfmax": DivideAttributesHF.MFMAX.value,
        "uadj": DivideAttributesHF.UADJ.value,
        "soil_params.b": DivideAttributesHF.BEXP.value,
        "soil_params.satdk": DivideAttributesHF.DKSAT.value,
        "soil_params.satpsi": DivideAttributesHF.PSISAT.value,
        "soil_params.slop": DivideAttributesHF.SLOPE_1KM.value,
        "soil_params.smcmax": DivideAttributesHF.SMCMAX.value,
        "soil_params.wltsmc": DivideAttributesHF.SMCWLT.value,
        "max_gw_storage": DivideAttributesHF.ZMAX.value,
        "Cgw": DivideAttributesHF.COEFF.value,
        "expon": DivideAttributesHF.EXPON.value,
    }


class LASAMParameters:
    """LASAM paramters based on soil type (ISLTYP) from https://github.com/NOAA-OWP/LGAR-C/blob/master/data/README.md"""

    lasam_params = {
        "isltyp_mode": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "theta_r": [0.05, 0.05, 0.04, 0.07, 0.05, 0.06, 0.06, 0.09, 0.08, 0.12, 0.11, 0.1],
        "theta_e": [0.38, 0.39, 0.39, 0.44, 0.49, 0.4, 0.38, 0.48, 0.44, 0.39, 0.48, 0.46],
        "alpha": [0.04, 0.03, 0.03, 0.01, 0.01, 0.01, 0.02, 0.01, 0.02, 0.03, 0.02, 0.01],
        "n": [
            3.18,
            1.75,
            1.45,
            1.66,
            1.68,
            1.47,
            1.33,
            1.52,
            1.42,
            1.21,
            1.32,
            1.25,
        ],
        "Ks": [26.64, 4.32, 1.584, 0.756, 1.836, 0.504, 0.54, 0.468, 0.3348, 0.468, 0.432, 0.612],
    }
