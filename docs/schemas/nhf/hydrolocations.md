???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | hy_id | integer | Hydrolocations identifier |
    | dn_nex_id | integer | Downstream nexus identifier |
    | dn_virtual_nex_id | number | Downstream virtual nexus identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "hy_id": {
                "type": "integer",
                "description": "Hydrolocations identifier"
            },
            "dn_nex_id": {
                "type": "integer",
                "description": "Downstream nexus identifier"
            },
            "dn_virtual_nex_id": {
                "type": "number",
                "description": "Downstream virtual nexus identifier"
            }
        },
        "required": [
            "hy_id"
        ]
    }
    ```
