???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | nhf_lake_id | integer | Unique NHF lake identifier |
    | ref_fp_id | number | Reference flowpath identifier |
    | hy_id | integer | Hydrolocation identifier |
    | fp_id | number | Flowpath identifier |
    | virtual_fp_id | integer | Virtual flowpath identifier |
    | dn_nex_id | number | Downstream nexus identifier |
    | dn_virtual_nex_id | integer | Downstream virtual nexus identifier |
    | div_id | integer | Associated divide identifier |
    | lake_id | string | Lake identifier |
    | res_id | string | Reservoir identifier |
    | LkArea | number | Lake area |
    | LkMxE | number | Lake maximum elevation |
    | WeirC | number | Weir coefficient |
    | WeirL | number | Weir length |
    | WeirE | number | Weir elevation |
    | OrificeC | number | Orifice coefficient |
    | OrificeA | number | Orifice area |
    | OrificeE | number | Orifice elevation |
    | Dam_Length | number | Dam length |
    | ifd | number | Initial flood depth |
    | reservoir_index_AnA | number | Reservoir index for AnA configuration |
    | reservoir_index_Extended_AnA | number | Reservoir index for Extended AnA configuration |
    | reservoir_index_GDL_AK | number | Reservoir index for GDL AK configuration |
    | reservoir_index_Medium_Range | number | Reservoir index for Medium Range configuration |
    | reservoir_index_Short_Range | number | Reservoir index for Short Range configuration |
    | dam_id | string | Dam identifier |
    | nidid | string | National Inventory of Dams identifier |
    | geometry | string | Spatial Geometry (POINT format) - stored in WKB binary format |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "nhf_lake_id": {
                "type": "integer",
                "description": "Unique NHF lake identifier"
            },
            "ref_fp_id": {
                "type": "number",
                "description": "Reference flowpath identifier"
            },
            "hy_id": {
                "type": "integer",
                "description": "Hydrolocation identifier"
            },
            "fp_id": {
                "type": "number",
                "description": "Flowpath identifier"
            },
            "virtual_fp_id": {
                "type": "integer",
                "description": "Virtual flowpath identifier"
            },
            "dn_nex_id": {
                "type": "number",
                "description": "Downstream nexus identifier"
            },
            "dn_virtual_nex_id": {
                "type": "integer",
                "description": "Downstream virtual nexus identifier"
            },
            "div_id": {
                "type": "integer",
                "description": "Associated divide identifier"
            },
            "lake_id": {
                "type": "string",
                "description": "Lake identifier"
            },
            "res_id": {
                "type": "string",
                "description": "Reservoir identifier"
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
            "OrificeC": {
                "type": "number",
                "description": "Orifice coefficient"
            },
            "OrificeA": {
                "type": "number",
                "description": "Orifice area"
            },
            "OrificeE": {
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
            "reservoir_index_AnA": {
                "type": "number",
                "description": "Reservoir index for AnA configuration"
            },
            "reservoir_index_Extended_AnA": {
                "type": "number",
                "description": "Reservoir index for Extended AnA configuration"
            },
            "reservoir_index_GDL_AK": {
                "type": "number",
                "description": "Reservoir index for GDL AK configuration"
            },
            "reservoir_index_Medium_Range": {
                "type": "number",
                "description": "Reservoir index for Medium Range configuration"
            },
            "reservoir_index_Short_Range": {
                "type": "number",
                "description": "Reservoir index for Short Range configuration"
            },
            "dam_id": {
                "type": "string",
                "description": "Dam identifier"
            },
            "nidid": {
                "type": "string",
                "description": "National Inventory of Dams identifier"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (POINT format) - stored in WKB binary format"
            }
        },
        "required": [
            "nhf_lake_id"
        ]
    }
    ```
