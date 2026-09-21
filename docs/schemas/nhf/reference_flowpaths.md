???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | ref_fp_id | integer | A flowpath ID from the full, reference hydrofabric dataset |
    | fp_id | integer | A flowpath ID from the flowpath table that was derived from the reference flowpath ID |
    | virtual_fp_id | integer | Virtual flowpath identifier |
    | div_id | integer | Associated divide identifier |
    | mainstem_virtual_fp_id | integer | Mainstem virtual flowpath identifier |
    | segment_order | integer | Segment order |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "ref_fp_id": {
                "type": "integer",
                "description": "A flowpath ID from the full, reference hydrofabric dataset"
            },
            "fp_id": {
                "type": "integer",
                "description": "A flowpath ID from the flowpath table that was derived from the reference flowpath ID"
            },
            "virtual_fp_id": {
                "type": "integer",
                "description": "Virtual flowpath identifier"
            },
            "div_id": {
                "type": "integer",
                "description": "Associated divide identifier"
            },
            "mainstem_virtual_fp_id": {
                "type": "integer",
                "description": "Mainstem virtual flowpath identifier"
            },
            "segment_order": {
                "type": "integer",
                "description": "Segment order"
            },
            "gid": {
                "type": "string",
                "description": "Geolocation Plus Code identifier"
            }
        },
        "required": [
            "ref_fp_id"
        ]
    }
    ```
