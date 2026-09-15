???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | link | string |  |
    | to | string |  |
    | Length_m | number |  |
    | alt | number |  |
    | So | number |  |
    | MusX | number |  |
    | MusK | number |  |
    | gage | string |  |
    | gage_nex_id | string |  |
    | WaterbodyID | string |  |
    | waterbody_nex_id | string |  |
    | id | string |  |
    | toid | string |  |
    | vpuid | string |  |
    | n | number |  |
    | BtmWdth | number |  |
    | TopWdth | number |  |
    | ChSlp | number |  |
    | nCC | number |  |
    | TopWdthCC | number |  |
    | Y | number |  |
    | YCC | number |  |
    | dingman_r | number |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "link": {
                "type": "string"
            },
            "to": {
                "type": "string"
            },
            "Length_m": {
                "type": "number"
            },
            "alt": {
                "type": "number"
            },
            "So": {
                "type": "number"
            },
            "MusX": {
                "type": "number"
            },
            "MusK": {
                "type": "number"
            },
            "gage": {
                "type": "string"
            },
            "gage_nex_id": {
                "type": "string"
            },
            "WaterbodyID": {
                "type": "string"
            },
            "waterbody_nex_id": {
                "type": "string"
            },
            "id": {
                "type": "string"
            },
            "toid": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            },
            "n": {
                "type": "number"
            },
            "BtmWdth": {
                "type": "number"
            },
            "TopWdth": {
                "type": "number"
            },
            "ChSlp": {
                "type": "number"
            },
            "nCC": {
                "type": "number"
            },
            "TopWdthCC": {
                "type": "number"
            },
            "Y": {
                "type": "number"
            },
            "YCC": {
                "type": "number"
            },
            "dingman_r": {
                "type": "number"
            }
        },
        "required": [
            "id",
            "toid",
            "vpuid"
        ]
    }
    ```
