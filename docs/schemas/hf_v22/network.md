???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | id | string |  |
    | toid | string |  |
    | divide_id | string |  |
    | ds_id | number |  |
    | mainstem | number |  |
    | hydroseq | number |  |
    | hf_source | string |  |
    | hf_id | number |  |
    | lengthkm | number |  |
    | areasqkm | number |  |
    | tot_drainage_areasqkm | number |  |
    | type | string |  |
    | vpuid | string |  |
    | hf_hydroseq | number |  |
    | hf_lengthkm | number |  |
    | hf_mainstem | number |  |
    | topo | string |  |
    | poi_id | number |  |
    | hl_uri | string |  |

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
            "divide_id": {
                "type": "string"
            },
            "ds_id": {
                "type": "number"
            },
            "mainstem": {
                "type": "number"
            },
            "hydroseq": {
                "type": "number"
            },
            "hf_source": {
                "type": "string"
            },
            "hf_id": {
                "type": "number"
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
            "type": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            },
            "hf_hydroseq": {
                "type": "number"
            },
            "hf_lengthkm": {
                "type": "number"
            },
            "hf_mainstem": {
                "type": "number"
            },
            "topo": {
                "type": "string"
            },
            "poi_id": {
                "type": "number"
            },
            "hl_uri": {
                "type": "string"
            }
        }
    }
    ```
