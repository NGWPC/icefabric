???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | nhf_lake_id | integer | NHF lake identifier |
    | lake_id | string | Source lake identifier |
    | virtual_fp_id | number | Associated virtual flowpath identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "nhf_lake_id": {
                "type": "integer",
                "description": "NHF lake identifier"
            },
            "lake_id": {
                "type": "string",
                "description": "Source lake identifier"
            },
            "virtual_fp_id": {
                "type": "number",
                "description": "Associated virtual flowpath identifier"
            }
        },
        "required": [
            "nhf_lake_id",
            "lake_id"
        ]
    }
    ```
