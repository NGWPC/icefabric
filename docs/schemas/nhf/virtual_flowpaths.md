???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | virtual_fp_id | integer | Virtual flowpath identifier |
    | dn_virtual_nex_id | integer | Downstream virtual nexus identifier |
    | up_virtual_nex_id | number | Upstream virtual nexus identifier |
    | segment_order | integer | Segment order |
    | length_km | number | Flowpath length [in kilometers] |
    | area_sqkm | number | Incremental areas of divide [in square kilometers] |
    | percentage_area_contribution | number | Percentage area contribution |
    | vpu_id | string | Vector Processing Unit identifier |
    | geometry | string | Spatial Geometry (MULTILINESTRING format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "virtual_fp_id": {
                "type": "integer",
                "description": "Virtual flowpath identifier"
            },
            "dn_virtual_nex_id": {
                "type": "integer",
                "description": "Downstream virtual nexus identifier"
            },
            "up_virtual_nex_id": {
                "type": "number",
                "description": "Upstream virtual nexus identifier"
            },
            "segment_order": {
                "type": "integer",
                "description": "Segment order"
            },
            "length_km": {
                "type": "number",
                "description": "Flowpath length [in kilometers]"
            },
            "area_sqkm": {
                "type": "number",
                "description": "Incremental areas of divide [in square kilometers]"
            },
            "percentage_area_contribution": {
                "type": "number",
                "description": "Percentage area contribution"
            },
            "vpu_id": {
                "type": "string",
                "description": "Vector Processing Unit identifier"
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
            }
        },
        "required": [
            "virtual_fp_id"
        ]
    }
    ```
