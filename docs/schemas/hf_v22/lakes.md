???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | lake_id | number |  |
    | LkArea | number |  |
    | LkMxE | number |  |
    | WeirC | number |  |
    | WeirL | number |  |
    | OrificeC | number |  |
    | OrificeA | number |  |
    | OrificeE | number |  |
    | WeirE | number |  |
    | ifd | number |  |
    | Dam_Length | number |  |
    | domain | string |  |
    | poi_id | integer |  |
    | hf_id | number |  |
    | reservoir_index_AnA | number |  |
    | reservoir_index_Extended_AnA | number |  |
    | reservoir_index_GDL_AK | number |  |
    | reservoir_index_Medium_Range | number |  |
    | reservoir_index_Short_Range | number |  |
    | res_id | string |  |
    | vpuid | string |  |
    | lake_x | number |  |
    | lake_y | number |  |
    | geometry | string |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "lake_id": {
                "type": "number"
            },
            "LkArea": {
                "type": "number"
            },
            "LkMxE": {
                "type": "number"
            },
            "WeirC": {
                "type": "number"
            },
            "WeirL": {
                "type": "number"
            },
            "OrificeC": {
                "type": "number"
            },
            "OrificeA": {
                "type": "number"
            },
            "OrificeE": {
                "type": "number"
            },
            "WeirE": {
                "type": "number"
            },
            "ifd": {
                "type": "number"
            },
            "Dam_Length": {
                "type": "number"
            },
            "domain": {
                "type": "string"
            },
            "poi_id": {
                "type": "integer"
            },
            "hf_id": {
                "type": "number"
            },
            "reservoir_index_AnA": {
                "type": "number"
            },
            "reservoir_index_Extended_AnA": {
                "type": "number"
            },
            "reservoir_index_GDL_AK": {
                "type": "number"
            },
            "reservoir_index_Medium_Range": {
                "type": "number"
            },
            "reservoir_index_Short_Range": {
                "type": "number"
            },
            "res_id": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            },
            "lake_x": {
                "type": "number"
            },
            "lake_y": {
                "type": "number"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream"
            }
        },
        "required": [
            "poi_id",
            "vpuid"
        ]
    }
    ```
