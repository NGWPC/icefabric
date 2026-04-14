from .hydrofabric_update import (
    NHD,
    Divides,
    Flowpaths,
    Gages,
    Hydrolocations,
    Lakes,
    Nexus,
    ReferenceFlowpaths,
    VirtualFlowpaths,
    VirtualNexus,
    Waterbodies,
)

nhf_layers = {
    "divides": Divides,
    "flowpaths": Flowpaths,
    "nexus": Nexus,
    "reference_flowpaths": ReferenceFlowpaths,
    "waterbodies": Waterbodies,
    "gages": Gages,
    "virtual_flowpaths": VirtualFlowpaths,
    "virtual_nexus": VirtualNexus,
    "hydrolocations": Hydrolocations,
    "lakes": Lakes,
    "nhd": NHD,
}
