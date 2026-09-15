???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | divide_id | string |  |
    | mode.bexp_soil_layers_stag=1 | number |  |
    | mode.bexp_soil_layers_stag=2 | number |  |
    | mode.bexp_soil_layers_stag=3 | number |  |
    | mode.bexp_soil_layers_stag=4 | number |  |
    | mode.ISLTYP | number |  |
    | mode.IVGTYP | number |  |
    | geom_mean.dksat_soil_layers_stag=1 | number |  |
    | geom_mean.dksat_soil_layers_stag=2 | number |  |
    | geom_mean.dksat_soil_layers_stag=3 | number |  |
    | geom_mean.dksat_soil_layers_stag=4 | number |  |
    | geom_mean.psisat_soil_layers_stag=1 | number |  |
    | geom_mean.psisat_soil_layers_stag=2 | number |  |
    | geom_mean.psisat_soil_layers_stag=3 | number |  |
    | geom_mean.psisat_soil_layers_stag=4 | number |  |
    | mean.cwpvt | number |  |
    | mean.mfsno | number |  |
    | mean.mp | number |  |
    | mean.refkdt | number |  |
    | mean.slope_1km | number |  |
    | mean.smcmax_soil_layers_stag=1 | number |  |
    | mean.smcmax_soil_layers_stag=2 | number |  |
    | mean.smcmax_soil_layers_stag=3 | number |  |
    | mean.smcmax_soil_layers_stag=4 | number |  |
    | mean.smcwlt_soil_layers_stag=1 | number |  |
    | mean.smcwlt_soil_layers_stag=2 | number |  |
    | mean.smcwlt_soil_layers_stag=3 | number |  |
    | mean.smcwlt_soil_layers_stag=4 | number |  |
    | mean.vcmx25 | number |  |
    | mean.Coeff | number |  |
    | mean.Zmax | number |  |
    | mode.Expon | number |  |
    | centroid_x | number |  |
    | centroid_y | number |  |
    | mean.impervious | number |  |
    | mean.elevation | number |  |
    | mean.slope | number |  |
    | circ_mean.aspect | number |  |
    | dist_4.twi | string |  |
    | vpuid | string |  |
    | glacier_percent | number |  |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "divide_id": {
                "type": "string"
            },
            "mode.bexp_soil_layers_stag=1": {
                "type": "number"
            },
            "mode.bexp_soil_layers_stag=2": {
                "type": "number"
            },
            "mode.bexp_soil_layers_stag=3": {
                "type": "number"
            },
            "mode.bexp_soil_layers_stag=4": {
                "type": "number"
            },
            "mode.ISLTYP": {
                "type": "number"
            },
            "mode.IVGTYP": {
                "type": "number"
            },
            "geom_mean.dksat_soil_layers_stag=1": {
                "type": "number"
            },
            "geom_mean.dksat_soil_layers_stag=2": {
                "type": "number"
            },
            "geom_mean.dksat_soil_layers_stag=3": {
                "type": "number"
            },
            "geom_mean.dksat_soil_layers_stag=4": {
                "type": "number"
            },
            "geom_mean.psisat_soil_layers_stag=1": {
                "type": "number"
            },
            "geom_mean.psisat_soil_layers_stag=2": {
                "type": "number"
            },
            "geom_mean.psisat_soil_layers_stag=3": {
                "type": "number"
            },
            "geom_mean.psisat_soil_layers_stag=4": {
                "type": "number"
            },
            "mean.cwpvt": {
                "type": "number"
            },
            "mean.mfsno": {
                "type": "number"
            },
            "mean.mp": {
                "type": "number"
            },
            "mean.refkdt": {
                "type": "number"
            },
            "mean.slope_1km": {
                "type": "number"
            },
            "mean.smcmax_soil_layers_stag=1": {
                "type": "number"
            },
            "mean.smcmax_soil_layers_stag=2": {
                "type": "number"
            },
            "mean.smcmax_soil_layers_stag=3": {
                "type": "number"
            },
            "mean.smcmax_soil_layers_stag=4": {
                "type": "number"
            },
            "mean.smcwlt_soil_layers_stag=1": {
                "type": "number"
            },
            "mean.smcwlt_soil_layers_stag=2": {
                "type": "number"
            },
            "mean.smcwlt_soil_layers_stag=3": {
                "type": "number"
            },
            "mean.smcwlt_soil_layers_stag=4": {
                "type": "number"
            },
            "mean.vcmx25": {
                "type": "number"
            },
            "mean.Coeff": {
                "type": "number"
            },
            "mean.Zmax": {
                "type": "number"
            },
            "mode.Expon": {
                "type": "number"
            },
            "centroid_x": {
                "type": "number"
            },
            "centroid_y": {
                "type": "number"
            },
            "mean.impervious": {
                "type": "number"
            },
            "mean.elevation": {
                "type": "number"
            },
            "mean.slope": {
                "type": "number"
            },
            "circ_mean.aspect": {
                "type": "number"
            },
            "dist_4.twi": {
                "type": "string"
            },
            "vpuid": {
                "type": "string"
            },
            "glacier_percent": {
                "type": "number"
            }
        },
        "required": [
            "divide_id",
            "vpuid"
        ]
    }
    ```
