"""Contains all schemas and enums for the RAS cross-sections"""

from enum import Enum


class XsType(str, Enum):
    """The domains used when querying the cross-sections.

    Attributes
    ----------
    CONFLATED : str
        HEC-RAS data mapped to nearest hydrofabric flowpath.
    REPRESENTATIVE : str
        The median, representative, cross-sections - derived from
        the conflated data set. Used as training/testing inputs for RiverML.
    """

    CONFLATED = "conflated"
    REPRESENTATIVE = "representative"
