import pandas as pd


def three_dim_flowpath_legend(upper_bound=6.5):
    """HTML legend for the 3D flowpath depth gradient."""
    return f"""
        <div style="
            display: flex;
            align-items: left;
            flex-direction: column;
            gap: 5px;
            font-family: sans-serif;
        ">
            <div style="display: flex; justify-content: space-between; width:200px; font-size: 16px;">
                <span></span>
                <span>Depth (m)</span>
                <span></span>
            </div>
            <div style="
                background: linear-gradient(to right, #7073FF, #0B0B1B);
                height: 20px;
                width: 200px;
                border: 1px solid #ccc;
            "></div>
            <div style="display: flex; justify-content: space-between; width:200px; font-size: 12px;">
                <span>0</span>
                <span>&rarr;</span>
                <span>{upper_bound}</span>
            </div>
        </div>
        """


bbox_examples = pd.DataFrame(
    {
        "Ex. 1": [31.3323, -109.0502, 37.0002, -103.0020],
        "Ex. 2": [35.8000, -106.7000, 37.0002, -105.5000],
        "Ex. 3": [34.9950, -106.8040, 35.2320, -106.4630],
    },
    index=["Min. Latitude (°)", "Min. Longitude (°)", "Max. Latitude (°)", "Max. Longitude (°)"],
)

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

three_dim_flowpath_tooltip = """The 3D Flowpaths map layer visualizes flowpath width and depth.
- __depth__ (meters) - represented by the `y_ml` attribute in the flowpath data. The depth is visualized as a color gradient, with deeper flowpaths shown in darker colors. *NOTE: White flowpaths indicate missing data.*
- __width__ (meters) - represented by the `topwdth` attribute in the flowpath data. The width is visualized as stream thickness.
"""
