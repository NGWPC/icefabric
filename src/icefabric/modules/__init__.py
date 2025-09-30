"""Contains helper functions to support NWM modules"""

import enum

from .create_ipes import (
    get_cfe_parameters,
    get_lasam_parameters,
    get_lstm_parameters,
    get_noahowp_parameters,
    get_sacsma_parameters,
    get_sft_parameters,
    get_smp_parameters,
    get_snow17_parameters,
    get_topmodel_parameters,
    get_topoflow_parameters,
    get_troute_parameters,
    get_ueb_parameters,
)
from .rnr import get_rnr_segment


class NWMModules(enum.Enum):
    """A list of all supported NWM Modules"""

    SFT = "sft"
    LSTM = "lstm"
    LASAM = "lasam"
    NOAHOWP = "noah_owp"
    SMP = "smp"
    SNOW17 = "snow17"
    SACSMA = "sacsma"
    TROUTE = "troute"
    TOPMODEL = "topmodel"
    TOPOFLOW = "topoflow"
    UEB = "ueb"
    CFE = "cfe"


class SmpModules(str, enum.Enum):
    """Enum class for defining acceptable inputs for the SMP 'module' variable"""

    cfe_s = "CFE-S"
    cfe_x = "CFE-X"
    lasam = "LASAM"
    topmodel = "TopModel"


modules_with_extra_args = {
    "sft": ["use_schaake"],
    "snow17": ["envca"],
    "sacsma": ["envca"],
    "smp": ["module"],
    "cfe": ["cfe_version"],
    "lasam": ["sft_included", "soil_params_file"],
}


config_mapper = {
    "sft": get_sft_parameters,
    "lstm": get_lstm_parameters,
    "lasam": get_lasam_parameters,
    "noah_owp": get_noahowp_parameters,
    "smp": get_smp_parameters,
    "snow17": get_snow17_parameters,
    "sacsma": get_sacsma_parameters,
    "troute": get_troute_parameters,
    "topmodel": get_topmodel_parameters,
    "topoflow": get_topoflow_parameters,
    "ueb": get_ueb_parameters,
    "cfe": get_cfe_parameters,
}

__all__ = [
    "get_sft_parameters",
    "get_rnr_segment",
    "get_lstm_parameters",
    "get_lasam_parameters",
    "get_noahowp_parameters",
    "get_smp_parameters",
    "get_snow17_parameters",
    "get_sacsma_parameters",
    "get_troute_parameters",
    "get_topmodel_parameters",
    "get_topoflow_parameters",
    "get_ueb_parameters",
    "get_cfe_parameters",
]
