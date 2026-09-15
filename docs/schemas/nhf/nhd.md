???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | nhd_feature_id | integer | NHD flowpath ID |
    | ref_id | integer | Associated flowpath ID from the flowpath table |
    | percent_inside | number | Percentage of the length of a flowpath segment that falls inside a buffer around the reference flowpath |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "nhd_feature_id": {
                "type": "integer",
                "description": "NHD flowpath ID"
            },
            "ref_id": {
                "type": "integer",
                "description": "Associated flowpath ID from the flowpath table"
            },
            "percent_inside": {
                "type": "number",
                "description": "Percentage of the length of a flowpath segment that falls inside a buffer around the reference flowpath"
            }
        },
        "required": [
            "ref_id"
        ]
    }
    ```
