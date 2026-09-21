???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | divide_id | string |  |
    | toid | string |  |
    | type | string |  |
    | ds_id | number |  |
    | areasqkm | number |  |
    | vpuid | string |  |
    | id | string |  |
    | lengthkm | number |  |
    | tot_drainage_areasqkm | number |  |
    | has_flowline | boolean |  |
    | geometry | string |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "divide_id": {
                "type": "string"
            },
            "toid": {
                "type": "string"
            },
            "type": {
                "type": "string"
            },
            "ds_id": {
                "type": "number"
            },
            "areasqkm": {
                "type": "number"
            },
            "vpuid": {
                "type": "string"
            },
            "id": {
                "type": "string"
            },
            "lengthkm": {
                "type": "number"
            },
            "tot_drainage_areasqkm": {
                "type": "number"
            },
            "has_flowline": {
                "type": "boolean"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream"
            }
        },
        "required": [
            "divide_id",
            "vpuid"
        ]
    }
    ```
