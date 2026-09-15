???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | lake_id | string | Source lake identifier |
    | virtual_fp_id | number | Associated virtual flowpath identifier |
    | nhf_lake_id | integer | NHF lake identifier |
    | source | string | Lake geometry source |
    | geometry | string | Spatial Geometry (MULTIPOLYGON format) stored as WKB |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "lake_id": {
                "type": "string",
                "description": "Source lake identifier"
            },
            "virtual_fp_id": {
                "type": "number",
                "description": "Associated virtual flowpath identifier"
            },
            "nhf_lake_id": {
                "type": "integer",
                "description": "NHF lake identifier"
            },
            "source": {
                "type": "string",
                "description": "Lake geometry source"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (MULTIPOLYGON format) stored as WKB"
            }
        },
        "required": [
            "lake_id",
            "nhf_lake_id"
        ]
    }
    ```
