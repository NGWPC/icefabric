import textwrap

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
            <div style="display: flex; justify-content: space-between; width:200px; font-size: 16px; font-weight: bold;">
                <span>Depth (m)</span>
                <span></span>
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
            <div style="
                background: white;
                height: 20px;
                width: 100px;
                border: 1px solid #ccc;
            "></div>
            <div style="display: flex; justify-content: space-between; width:100px; font-size: 12px;">
                <span></span>
                <span>No Data</span>
                <span></span>
            </div>
        </div>
        """


def three_dim_flowpath_tooltip(d_type="y_ml", w_type="topwdth"):
    """Return legend information for channel geometry layer."""
    base_data = "flowpath"
    if d_type != "y_ml" and w_type != "topwdth":
        base_data = "RAS XS"
    tooltip = textwrap.dedent(f"""\
        The Channel Geometry map layer (not selected by default - check box in layer control at bottom righthand corner of the map) visualizes flowpath width and depth.
        - __depth__ (meters) - represented by the `{d_type}` attribute in the {base_data} data. The depth is visualized as a color gradient, with deeper flowpaths shown in darker colors. *NOTE: White flowpaths indicate missing data.*
        - __width__ (meters) - represented by the `{w_type}` attribute in the {base_data} data. The width is visualized as stream thickness. The thicker the stream, the wider the channel. *NOTE: Flowpaths with missing `{w_type}` values are drawn with a dashed line.*
    """)
    return tooltip


bbox_examples = pd.DataFrame(
    {
        "Ex. 1": [31.3323, -109.0502, 37.0002, -103.0020],
        "Ex. 2": [35.8000, -106.7000, 37.0002, -105.5000],
        "Ex. 3": [34.9950, -106.8040, 35.2320, -106.4630],
    },
    index=["Min. Latitude (°)", "Min. Longitude (°)", "Max. Latitude (°)", "Max. Longitude (°)"],
)

query_type_tooltip = textwrap.dedent("""\
    The two query type options when subsetting the cross-sections.
    - `Flowpath` - Subset will include all cross-sections that belong/map to a reference hydrofabric flowpath ID.
    - `Bounding Box` - Subset will include all cross-sections that are fully contained within a defined lat/lon geospatial bounding box.
""")

domain_tooltip = textwrap.dedent("""\
    The two domain options when querying the cross-sections.
    - `conflated` - HEC-RAS data mapped to nearest hydrofabric flowpath.
    - `representative` - The median, representative, cross-sections - derived from the conflated data set. Used as training/testing inputs for RiverML.
""")

hf_subset_options_explanation = textwrap.dedent("""\
    - **Flowpath ID**: traces upstream from an origin flowpath - *e.g., 1275769040909371*
    - **Gage ID**: traces upstream from a USGS gage ID (maps to a flowpath) - *e.g., 01099500*
    - **VPU ID**: includes all HF features within a vector processing unit (VPU) - *e.g., 08*
""")

flowpath_id_tooltip = "A flowpath ID from the reference hydrofabric."

bounding_box_tooltip = textwrap.dedent("""\
    ###### Draw a defined rectangular bounding geometry on the map below.
    Only the most recently drawn/interacted-with rectangle will be considered. Edit or delete the drawing as needed.\\
    The coordinates will update below the map as you draw.\\
    The subset returned will include only cross-sections that fully fit into the bounding box.
    > IMPORTANT\\
    > The bounding box query option is best used for small, focused areas due to the large number of
    > cross-sections in the dataset and resulting processing time. You will be notified if your bounding
    > box query is too large to process.
""")
