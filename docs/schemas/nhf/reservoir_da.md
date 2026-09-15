???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | nhf_lake_id | integer | NHF lake identifier |
    | lake_id | string | Source lake identifier |
    | site_no | string | Associated gage site number |
    | da_type | integer | Drainage-area type |

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
            "site_no": {
                "type": "string",
                "description": "Associated gage site number"
            },
            "da_type": {
                "type": "integer",
                "description": "Drainage-area type"
            }
        },
        "required": [
            "nhf_lake_id",
            "lake_id"
        ]
    }
    ```
