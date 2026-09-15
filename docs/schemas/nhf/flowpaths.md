???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | fp_id | integer | Unique flowpath identifier |
    | dn_nex_id | integer | Connected downstream nexus identifier |
    | up_nex_id | number | Connected upstream nexus identifier |
    | div_id | integer | Associated divide identifier |
    | vpu_id | string | Associated Vector Processing Unit (VPU) identifier |
    | length_km | number | Flowpath length [in kilometers] |
    | area_sqkm | number | Associated catchement area of divide [in square kilometers] |
    | total_da_sqkm | number | Total upstream drainage area [in square kilometers] |
    | mainstem_lp | integer | Associated flowpath mainstem (primary downstream segment) |
    | path_length | number | Distance to outlet [in kilometers] |
    | dn_hydroseq | integer | Downstream hydrologic sequence |
    | hydroseq | integer | Hydrologic sequence number |
    | stream_order | integer | Strahler stream order |
    | mean_elevation | number | DEM derived mean elevation |
    | slope | number | DEM derived slope |
    | n | number | Manning's in channel roughness |
    | r | number | Estimated channel shape |
    | y | number | Estimated depth associated with top width |
    | ncc | number | Compound channel top width |
    | btmwdth | number | Bottom width of channel |
    | chslp | number | Channel side slope |
    | musx | number | Muskingum weighting factor |
    | musk | integer | Muskingum routing time |
    | topwdth | number | Top width |
    | topwdthcc | number | Compound channel top width |
    | topwdthcc_ml | number | Compound channel top width (derived from machine learning) |
    | topwdth_ml | number | Top width (derived from machine learning) |
    | y_ml | number | Estimated depth associated with top width (derived from machine learning) |
    | r_ml | number | Estimated channel shape (derived from machine learning) |
    | fp_to_id | integer | The flowpath ID that is downstream of the connected downstream nexus |
    | geometry | string | Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |
    | terminalpa | integer | Terminal path grouping identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "fp_id": {
                "type": "integer",
                "description": "Unique flowpath identifier"
            },
            "dn_nex_id": {
                "type": "integer",
                "description": "Connected downstream nexus identifier"
            },
            "up_nex_id": {
                "type": "number",
                "description": "Connected upstream nexus identifier"
            },
            "div_id": {
                "type": "integer",
                "description": "Associated divide identifier"
            },
            "vpu_id": {
                "type": "string",
                "description": "Associated Vector Processing Unit (VPU) identifier"
            },
            "length_km": {
                "type": "number",
                "description": "Flowpath length [in kilometers]"
            },
            "area_sqkm": {
                "type": "number",
                "description": "Associated catchement area of divide [in square kilometers]"
            },
            "total_da_sqkm": {
                "type": "number",
                "description": "Total upstream drainage area [in square kilometers]"
            },
            "mainstem_lp": {
                "type": "integer",
                "description": "Associated flowpath mainstem (primary downstream segment)"
            },
            "path_length": {
                "type": "number",
                "description": "Distance to outlet [in kilometers]"
            },
            "dn_hydroseq": {
                "type": "integer",
                "description": "Downstream hydrologic sequence"
            },
            "hydroseq": {
                "type": "integer",
                "description": "Hydrologic sequence number"
            },
            "stream_order": {
                "type": "integer",
                "description": "Strahler stream order"
            },
            "mean_elevation": {
                "type": "number",
                "description": "DEM derived mean elevation"
            },
            "slope": {
                "type": "number",
                "description": "DEM derived slope"
            },
            "n": {
                "type": "number",
                "description": "Manning's in channel roughness"
            },
            "r": {
                "type": "number",
                "description": "Estimated channel shape"
            },
            "y": {
                "type": "number",
                "description": "Estimated depth associated with top width"
            },
            "ncc": {
                "type": "number",
                "description": "Compound channel top width"
            },
            "btmwdth": {
                "type": "number",
                "description": "Bottom width of channel"
            },
            "chslp": {
                "type": "number",
                "description": "Channel side slope"
            },
            "musx": {
                "type": "number",
                "description": "Muskingum weighting factor"
            },
            "musk": {
                "type": "integer",
                "description": "Muskingum routing time"
            },
            "topwdth": {
                "type": "number",
                "description": "Top width"
            },
            "topwdthcc": {
                "type": "number",
                "description": "Compound channel top width"
            },
            "topwdthcc_ml": {
                "type": "number",
                "description": "Compound channel top width (derived from machine learning)"
            },
            "topwdth_ml": {
                "type": "number",
                "description": "Top width (derived from machine learning)"
            },
            "y_ml": {
                "type": "number",
                "description": "Estimated depth associated with top width (derived from machine learning)"
            },
            "r_ml": {
                "type": "number",
                "description": "Estimated channel shape (derived from machine learning)"
            },
            "fp_to_id": {
                "type": "integer",
                "description": "The flowpath ID that is downstream of the connected downstream nexus"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format"
            },
            "gid": {
                "type": "string",
                "description": "Geolocation Plus Code identifier"
            },
            "terminalpa": {
                "type": "integer",
                "description": "Terminal path grouping identifier"
            }
        },
        "required": [
            "fp_id"
        ]
    }
    ```
