???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | wb_id | integer | Unique waterbody identifier |
    | fp_id | number | Associated flowpath identifier |
    | hy_id | integer | Hydrolocation identifier |
    | ref_fp_id | number | Reference flowpath identifier |
    | dam_id | string | Dam identifier |
    | dam_name | string | Dam name |
    | dam_type | string | Dam type |
    | LkArea | number | Lake area |
    | LkMxE | number | Lake maximum elevation |
    | WeirC | number | Weir coefficient |
    | WeirL | number | Weir length |
    | WeirE | number | Weir elevation |
    | OrficeC | number | Orifice coefficient |
    | OrficeA | number | Orifice area |
    | OrficeE | number | Orifice elevation |
    | Dam_Length | number | Dam length |
    | ifd | number | Initial flood depth |
    | div_id | number | Associated divide identifier |
    | dn_nex_id | number | Downstream nexus identifier |
    | dn_virtual_nex_id | number | Downstream virtual nexus identifier |
    | virtual_fp_id | number | Virtual flowpath identifier |
    | geometry | string | Spatial Geometry (POLYGON format) - stored in WKB binary format |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "wb_id": {
                "type": "integer",
                "description": "Unique waterbody identifier"
            },
            "fp_id": {
                "type": "number",
                "description": "Associated flowpath identifier"
            },
            "hy_id": {
                "type": "integer",
                "description": "Hydrolocation identifier"
            },
            "ref_fp_id": {
                "type": "number",
                "description": "Reference flowpath identifier"
            },
            "dam_id": {
                "type": "string",
                "description": "Dam identifier"
            },
            "dam_name": {
                "type": "string",
                "description": "Dam name"
            },
            "dam_type": {
                "type": "string",
                "description": "Dam type"
            },
            "LkArea": {
                "type": "number",
                "description": "Lake area"
            },
            "LkMxE": {
                "type": "number",
                "description": "Lake maximum elevation"
            },
            "WeirC": {
                "type": "number",
                "description": "Weir coefficient"
            },
            "WeirL": {
                "type": "number",
                "description": "Weir length"
            },
            "WeirE": {
                "type": "number",
                "description": "Weir elevation"
            },
            "OrficeC": {
                "type": "number",
                "description": "Orifice coefficient"
            },
            "OrficeA": {
                "type": "number",
                "description": "Orifice area"
            },
            "OrficeE": {
                "type": "number",
                "description": "Orifice elevation"
            },
            "Dam_Length": {
                "type": "number",
                "description": "Dam length"
            },
            "ifd": {
                "type": "number",
                "description": "Initial flood depth"
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
            "virtual_fp_id": {
                "type": "number",
                "description": "Virtual flowpath identifier"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (POLYGON format) - stored in WKB binary format"
            }
        },
        "required": [
            "wb_id"
        ]
    }
    ```
