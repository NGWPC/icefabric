???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | nex_id | integer | Unique nexus identifier |
    | dn_fp_id | integer | Associated downstream flowpath identifier |
    | vpu_id | string | Vector Processing Unit identifier |
    | geometry | string | Spatial Geometry (POINT format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "nex_id": {
                "type": "integer",
                "description": "Unique nexus identifier"
            },
            "dn_fp_id": {
                "type": "integer",
                "description": "Associated downstream flowpath identifier"
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
            "nex_id"
        ]
    }
    ```
