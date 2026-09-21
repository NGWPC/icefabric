???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | virtual_nex_id | integer | Virtual nexus identifier |
    | dn_virtual_fp_id | integer | Downstream virtual flowpath identifier |
    | vpu_id | string | Vector Processing Unit identifier |
    | geometry | string | Spatial Geometry (POINT format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "virtual_nex_id": {
                "type": "integer",
                "description": "Virtual nexus identifier"
            },
            "dn_virtual_fp_id": {
                "type": "integer",
                "description": "Downstream virtual flowpath identifier"
            },
            "vpu_id": {
                "type": "string",
                "description": "Vector Processing Unit identifier"
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
            "virtual_nex_id"
        ]
    }
    ```
