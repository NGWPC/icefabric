???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | id | string |  |
    | toid | string |  |
    | mainstem | number |  |
    | order | number |  |
    | hydroseq | integer |  |
    | lengthkm | number |  |
    | areasqkm | number |  |
    | tot_drainage_areasqkm | number |  |
    | has_divide | boolean |  |
    | divide_id | string |  |
    | poi_id | string |  |
    | vpuid | string |  |
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
            "mainstem": {
                "type": "number"
            },
            "order": {
                "type": "number"
            },
            "hydroseq": {
                "type": "integer"
            },
            "lengthkm": {
                "type": "number"
            },
            "areasqkm": {
                "type": "number"
            },
            "tot_drainage_areasqkm": {
                "type": "number"
            },
            "has_divide": {
                "type": "boolean"
            },
            "divide_id": {
                "type": "string"
            },
            "poi_id": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
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
            "divide_id",
            "vpuid"
        ]
    }
    ```
