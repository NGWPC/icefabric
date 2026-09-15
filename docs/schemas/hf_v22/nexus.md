???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | id | string |  |
    | toid | string |  |
    | type | string |  |
    | vpuid | string |  |
    | poi_id | number |  |
    | geometry | string |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "id": {
                "type": "string"
            },
            "toid": {
                "type": "string"
            },
            "type": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            },
            "poi_id": {
                "type": "number"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream"
            }
        },
        "required": [
            "id",
            "toid",
            "vpuid"
        ]
    }
    ```
