???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | poi_id | integer |  |
    | id | string |  |
    | nex_id | string |  |
    | vpuid | string |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "poi_id": {
                "type": "integer"
            },
            "id": {
                "type": "string"
            },
            "nex_id": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            }
        },
        "required": [
            "poi_id",
            "id",
            "nex_id",
            "vpuid"
        ]
    }
    ```
