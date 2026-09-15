???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | poi_id | integer |  |
    | id | string |  |
    | nex_id | string |  |
    | hf_id | number |  |
    | hl_link | string |  |
    | hl_reference | string |  |
    | hl_uri | string |  |
    | hl_source | string |  |
    | hl_x | number |  |
    | hl_y | number |  |
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
            "hf_id": {
                "type": "number"
            },
            "hl_link": {
                "type": "string"
            },
            "hl_reference": {
                "type": "string"
            },
            "hl_uri": {
                "type": "string"
            },
            "hl_source": {
                "type": "string"
            },
            "hl_x": {
                "type": "number"
            },
            "hl_y": {
                "type": "number"
            },
            "vpuid": {
                "type": "string"
            }
        },
        "required": [
            "id",
            "nex_id",
            "vpuid"
        ]
    }
    ```
