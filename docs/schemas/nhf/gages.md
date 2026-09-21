???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | site_no | string | USGS Site Number |
    | status | string | Gage Status |
    | hy_id | integer | Hydrolocation Identifier |
    | USGS_basin_km2 | number | USGS Basin Area in square kilometers |
    | ref_fp_id | integer | Reference Flowpath Identifier |
    | method_fp_to_gage | string | Method used to associate flowpath to gage |
    | fp_id | number | Flowpath Identifier |
    | virtual_fp_id | number | Virtual Flowpath Identifier |
    | div_id | number | Associated divide identifier |
    | dn_nex_id | number | Downstream nexus identifier |
    | dn_virtual_nex_id | number | Downstream virtual nexus identifier |
    | mainstem_virtual_fp_id | number | Mainstem virtual flowpath identifier |
    | segment_order | number | Segment order |
    | geometry | string | Spatial Geometry (POINT format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "site_no": {
                "type": "string",
                "description": "USGS Site Number"
            },
            "status": {
                "type": "string",
                "description": "Gage Status"
            },
            "hy_id": {
                "type": "integer",
                "description": "Hydrolocation Identifier"
            },
            "USGS_basin_km2": {
                "type": "number",
                "description": "USGS Basin Area in square kilometers"
            },
            "ref_fp_id": {
                "type": "integer",
                "description": "Reference Flowpath Identifier"
            },
            "method_fp_to_gage": {
                "type": "string",
                "description": "Method used to associate flowpath to gage"
            },
            "fp_id": {
                "type": "number",
                "description": "Flowpath Identifier"
            },
            "virtual_fp_id": {
                "type": "number",
                "description": "Virtual Flowpath Identifier"
            },
            "div_id": {
                "type": "number",
                "description": "Associated divide identifier"
            },
            "dn_nex_id": {
                "type": "number",
                "description": "Downstream nexus identifier"
            },
            "dn_virtual_nex_id": {
                "type": "number",
                "description": "Downstream virtual nexus identifier"
            },
            "mainstem_virtual_fp_id": {
                "type": "number",
                "description": "Mainstem virtual flowpath identifier"
            },
            "segment_order": {
                "type": "number",
                "description": "Segment order"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (POINT format) - stored in WKB binary format"
            },
            "gid": {
                "type": "string",
                "description": "Geolocation Plus Code identifier"
            }
        },
        "required": [
            "site_no"
        ]
    }
    ```
