query_type_tooltip = """
    The two query type options when subsetting the cross-sections.
    - `Flowpath` - Subset will include all cross-sections that belong/map to a reference hydrofabric flowpath ID.
    - `Bounding Box` - Subset will include all cross-sections that are fully contained within a defined lat/lon geospatial bounding box.
"""

domain_tooltip = """
    The two domain options when querying the cross-sections.
    - `conflated` - HEC-RAS data mapped to nearest hydrofabric flowpath.
    - `representative` - The median, representative, cross-sections - derived from the conflated data set. Used as training/testing inputs for RiverML.
"""

hf_subset_options_explanation = """
    - **Flowpath ID**: traces upstream from an origin flowpath - *e.g., 3490271*
    - **Gage ID**: traces upstream from a USGS gage ID (maps to a flowpath) - *e.g., 01010000*
    - **VPU ID**: includes all HF features within a vector processing unit (VPU) - *e.g., 08*
"""

flowpath_id_tooltip = "A flowpath ID from the reference hydrofabric."

bounding_box_tooltip = (
    "A defined rectangular bounding geometry.\n"
    "The min/max lat/lon coordinates should be in standard EPSG:4326 format.\n"
    "The subset returned will include only cross-sections that fully fit into the bounding box."
)
