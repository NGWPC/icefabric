"""Contains all schemas and enums for the RAS cross-sections"""

from enum import Enum


class XsType(str, Enum):
    """The domains used when querying the cross-sections.

    Attributes
    ----------
    MIP : str
        Mapping Information Platform
    BLE : str
        Base Level Engineering
    """

    MIP = "mip"
    BLE = "ble"
