from .hydrofabric import (
    DivideAttributes,
    FlowpathAttributes,
    FlowpathAttributesML,
    Network,
    POIs,
)
from .hydrofabric import (
    Divides as DividesV22,
)
from .hydrofabric import (
    Flowpaths as FlowpathsV22,
)
from .hydrofabric import (
    Hydrolocations as HydrolocationsV22,
)
from .hydrofabric import (
    Lakes as LakesV22,
)
from .hydrofabric import (
    Nexus as NexusV22,
)
from .hydrofabric_update import (
    NHD,
    Divides,
    Flowpaths,
    Gages,
    Hydrolocations,
    Lakes,
    LakesPolygons,
    LakeVFPCrosswalk,
    Nexus,
    ReferenceFlowpaths,
    ReservoirDA,
    VirtualFlowpaths,
    VirtualNexus,
)

nhf_layers = {
    "divides": Divides,
    "flowpaths": Flowpaths,
    "nexus": Nexus,
    "reference_flowpaths": ReferenceFlowpaths,
    "gages": Gages,
    "virtual_flowpaths": VirtualFlowpaths,
    "virtual_nexus": VirtualNexus,
    "lakes": Lakes,
    "hydrolocations": Hydrolocations,
    "nhd": NHD,
    "lakes_polygons": LakesPolygons,
    "reservoir_da": ReservoirDA,
    "lake_vfp_crosswalk": LakeVFPCrosswalk,
}

hf_layers = {
    "divide_attributes": DivideAttributes,
    "divides": DividesV22,
    "flowpath_attributes": FlowpathAttributes,
    "flowpath_attributes_ml": FlowpathAttributesML,
    "flowpaths": FlowpathsV22,
    "hydrolocations": HydrolocationsV22,
    "lakes": LakesV22,
    "network": Network,
    "nexus": NexusV22,
    "pois": POIs,
}
