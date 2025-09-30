"""Contains helper functions to support NWM modules"""

import enum

from .create_ipes import divide_parameters, get_sft_parameters
from .rnr import get_rnr_segment


class NWMModules(enum.Enum):
    """A list of all supported NWM Modules"""

    SFT = "sft"


config_mapper = {
    "sft": get_sft_parameters,
}

__all__ = [
    "divide_parameters",
    "get_sft_parameters",
    "get_rnr_segment",
]
