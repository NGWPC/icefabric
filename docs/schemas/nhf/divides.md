???+ abstract "Schema Definition Table"
    | Field | Type | Description |
    |-------|------|-------------|
    | div_id | integer | Unique divide identifier |
    | vpu_id | string | Vector Processing Unit identifier |
    | type | string | Divide Type (one of independent, aggregate, connectors) |
    | area_sqkm | number | Catchment area in sqkm |
    | bexp_mode | number | Pore size distribution index (exponential term) |
    | isltyp_mode | number | Dominent soil type category |
    | ivgtyp_mode | number | Dominent vegetation type category |
    | dksat_geomean | number | Saturated soil connectivity |
    | psisat_geomean | number | Saturated soil matric potential |
    | cwpvt_mean | number | Empirical canopy wind parameter |
    | mp_mean | number | Slope of conductance to photosynthesis relationship |
    | mfsno_mean | number | Snowmelt m parameter |
    | quartz_mean | number | Mean soil quartz content |
    | refkdt_mean | number | Surface runoff parameter, impacts surface infiltration |
    | slope1km_mean | number | Linear reservoir coefficient |
    | smcmax_mean | number | Saturated value of soil moisture |
    | smcwlt_mean | number | Wilting point soil moisture |
    | vcmx_mean | number | Maximum rate of carboxylation at 25 C |
    | imperv_mean | number | Percentage of catchment with an impervious surface |
    | twi_q25 | number | Topographic wetness index 1st quartile |
    | twi_q50 | number | Topographic wetness index 2nd quartile |
    | twi_q75 | number | Topographic wetness index 3rd quartile |
    | twi_q100 | number | Topographic wetness index 4th quartile |
    | twi_q10 | number | Topographic wetness index 10th percentile |
    | twi_q20 | number | Topographic wetness index 20th percentile |
    | twi_q30 | number | Topographic wetness index 30th percentile |
    | twi_q40 | number | Topographic wetness index 40th percentile |
    | twi_q60 | number | Topographic wetness index 60th percentile |
    | twi_q70 | number | Topographic wetness index 70th percentile |
    | twi_q80 | number | Topographic wetness index 80th percentile |
    | twi_q90 | number | Topographic wetness index 90th percentile |
    | elevation_mean | number | DEM derived mean divide elevation |
    | slope250m_mean | number | DEM derived mean divide slope |
    | aspect_circmean | number | DEM derived mean divide aspect |
    | lzfpm_mean | number | Maximum lower zone free water mean (primary) |
    | lzpk_mean | number | Lower zone recession coefficient mean (primary) |
    | lztwm_mean | number | Maximum lower zone tension water mean |
    | rexp_mean | number | Percolation equation exponent mean |
    | uzk_mean | number | Upper zone recession coefficient mean |
    | zperc_mean | number | Minimum percolation rate coefficient mean |
    | lzfsm_mean | number | Maximum lower zone free water mean (secondary aka supplemental) |
    | lzsk_mean | number | Lower zone recession coefficient mean, (secondary aka supplemental) |
    | pfree_mean | number | Fraction of water percolating from upper zone directly to lower zone free water storage (mean) |
    | uzfwm_mean | number | Maximum upper zone free water mean |
    | uztwm_mean | number | Upper zone tension water maximum storage mean |
    | mfmin_mean | number | Minimum non-rain melt factor mean |
    | mfmax_mean | number | Maximum non-rain melt factor mean |
    | uadj_mean | number | Average wind function for rain on snow (mean) |
    | a_xinanjiang_inflection_point_parameter | number | Inflection point parameter for the Xinanjiang runoff generation model configuration |
    | b_xinanjiang_shape_parameter | number | Main, exponential shape parameter for the Xinanjiang runoff generation model configuration |
    | x_xinanjiang_shape_parameter | number | Secondary, modifier shape parameter for the Xinanjiang runoff generation model configuration |
    | temp_delta_jan_mean | number | Difference between the normal high temp and the normal low temp for the month of January |
    | temp_delta_feb_mean | number | Difference between the normal high temp and the normal low temp for the month of February |
    | temp_delta_mar_mean | number | Difference between the normal high temp and the normal low temp for the month of March |
    | temp_delta_apr_mean | number | Difference between the normal high temp and the normal low temp for the month of April |
    | temp_delta_may_mean | number | Difference between the normal high temp and the normal low temp for the month of May |
    | temp_delta_jun_mean | number | Difference between the normal high temp and the normal low temp for the month of June |
    | temp_delta_jul_mean | number | Difference between the normal high temp and the normal low temp for the month of July |
    | temp_delta_aug_mean | number | Difference between the normal high temp and the normal low temp for the month of August |
    | temp_delta_sep_mean | number | Difference between the normal high temp and the normal low temp for the month of September |
    | temp_delta_oct_mean | number | Difference between the normal high temp and the normal low temp for the month of October |
    | temp_delta_nov_mean | number | Difference between the normal high temp and the normal low temp for the month of November |
    | temp_delta_dec_mean | number | Difference between the normal high temp and the normal low temp for the month of December |
    | lat | number | Latitude of the divide (in WGS84 degrees) |
    | lon | number | Longitude of the divide (in WGS84 degrees) |
    | glacier_percent | number | Percentage of glacier cover within the divide |
    | cgw | number | Groundwater Coefficient |
    | expon | number | Groundwater Exponent |
    | max_gw_storage | number | The maximum storage capacity (or total height) of the conceptual groundwater bucket |
    | vegetation_height | number | Vegetation height |
    | zero_plane_displacement_height | number | Zero-plane displacement height |
    | momentum_transfer_roughness_length | number | Momentum-transfer roughness length |
    | heat_transfer_roughness_length | number | Heat-transfer roughness length |
    | surface_longwave_emissivity | number | Surface longwave emissivity |
    | surface_shortwave_albedo | number | Surface shortwave albedo |
    | geometry | string | Spatial Geometry (MULTIPOLYGON format) - stored in WKB binary format |
    | gid | string | Geolocation Plus Code identifier |

???+ example "JSON Schema"
    ```json
    {
        "type": "object",
        "properties": {
            "div_id": {
                "type": "integer",
                "description": "Unique divide identifier"
            },
            "vpu_id": {
                "type": "string",
                "description": "Vector Processing Unit identifier"
            },
            "type": {
                "type": "string",
                "description": "Divide Type (one of independent, aggregate, connectors)"
            },
            "area_sqkm": {
                "type": "number",
                "description": "Catchment area in sqkm"
            },
            "bexp_mode": {
                "type": "number",
                "description": "Pore size distribution index (exponential term)"
            },
            "isltyp_mode": {
                "type": "number",
                "description": "Dominent soil type category"
            },
            "ivgtyp_mode": {
                "type": "number",
                "description": "Dominent vegetation type category"
            },
            "dksat_geomean": {
                "type": "number",
                "description": "Saturated soil connectivity"
            },
            "psisat_geomean": {
                "type": "number",
                "description": "Saturated soil matric potential"
            },
            "cwpvt_mean": {
                "type": "number",
                "description": "Empirical canopy wind parameter"
            },
            "mp_mean": {
                "type": "number",
                "description": "Slope of conductance to photosynthesis relationship"
            },
            "mfsno_mean": {
                "type": "number",
                "description": "Snowmelt m parameter"
            },
            "quartz_mean": {
                "type": "number",
                "description": "Mean soil quartz content"
            },
            "refkdt_mean": {
                "type": "number",
                "description": "Surface runoff parameter, impacts surface infiltration"
            },
            "slope1km_mean": {
                "type": "number",
                "description": "Linear reservoir coefficient"
            },
            "smcmax_mean": {
                "type": "number",
                "description": "Saturated value of soil moisture"
            },
            "smcwlt_mean": {
                "type": "number",
                "description": "Wilting point soil moisture"
            },
            "vcmx_mean": {
                "type": "number",
                "description": "Maximum rate of carboxylation at 25 C"
            },
            "imperv_mean": {
                "type": "number",
                "description": "Percentage of catchment with an impervious surface"
            },
            "twi_q25": {
                "type": "number",
                "description": "Topographic wetness index 1st quartile"
            },
            "twi_q50": {
                "type": "number",
                "description": "Topographic wetness index 2nd quartile"
            },
            "twi_q75": {
                "type": "number",
                "description": "Topographic wetness index 3rd quartile"
            },
            "twi_q100": {
                "type": "number",
                "description": "Topographic wetness index 4th quartile"
            },
            "twi_q10": {
                "type": "number",
                "description": "Topographic wetness index 10th percentile"
            },
            "twi_q20": {
                "type": "number",
                "description": "Topographic wetness index 20th percentile"
            },
            "twi_q30": {
                "type": "number",
                "description": "Topographic wetness index 30th percentile"
            },
            "twi_q40": {
                "type": "number",
                "description": "Topographic wetness index 40th percentile"
            },
            "twi_q60": {
                "type": "number",
                "description": "Topographic wetness index 60th percentile"
            },
            "twi_q70": {
                "type": "number",
                "description": "Topographic wetness index 70th percentile"
            },
            "twi_q80": {
                "type": "number",
                "description": "Topographic wetness index 80th percentile"
            },
            "twi_q90": {
                "type": "number",
                "description": "Topographic wetness index 90th percentile"
            },
            "elevation_mean": {
                "type": "number",
                "description": "DEM derived mean divide elevation"
            },
            "slope250m_mean": {
                "type": "number",
                "description": "DEM derived mean divide slope"
            },
            "aspect_circmean": {
                "type": "number",
                "description": "DEM derived mean divide aspect"
            },
            "lzfpm_mean": {
                "type": "number",
                "description": "Maximum lower zone free water mean (primary)"
            },
            "lzpk_mean": {
                "type": "number",
                "description": "Lower zone recession coefficient mean (primary)"
            },
            "lztwm_mean": {
                "type": "number",
                "description": "Maximum lower zone tension water mean"
            },
            "rexp_mean": {
                "type": "number",
                "description": "Percolation equation exponent mean"
            },
            "uzk_mean": {
                "type": "number",
                "description": "Upper zone recession coefficient mean"
            },
            "zperc_mean": {
                "type": "number",
                "description": "Minimum percolation rate coefficient mean"
            },
            "lzfsm_mean": {
                "type": "number",
                "description": "Maximum lower zone free water mean (secondary aka supplemental)"
            },
            "lzsk_mean": {
                "type": "number",
                "description": "Lower zone recession coefficient mean, (secondary aka supplemental)"
            },
            "pfree_mean": {
                "type": "number",
                "description": "Fraction of water percolating from upper zone directly to lower zone free water storage (mean)"
            },
            "uzfwm_mean": {
                "type": "number",
                "description": "Maximum upper zone free water mean"
            },
            "uztwm_mean": {
                "type": "number",
                "description": "Upper zone tension water maximum storage mean"
            },
            "mfmin_mean": {
                "type": "number",
                "description": "Minimum non-rain melt factor mean"
            },
            "mfmax_mean": {
                "type": "number",
                "description": "Maximum non-rain melt factor mean"
            },
            "uadj_mean": {
                "type": "number",
                "description": "Average wind function for rain on snow (mean)"
            },
            "a_xinanjiang_inflection_point_parameter": {
                "type": "number",
                "description": "Inflection point parameter for the Xinanjiang runoff generation model configuration"
            },
            "b_xinanjiang_shape_parameter": {
                "type": "number",
                "description": "Main, exponential shape parameter for the Xinanjiang runoff generation model configuration"
            },
            "x_xinanjiang_shape_parameter": {
                "type": "number",
                "description": "Secondary, modifier shape parameter for the Xinanjiang runoff generation model configuration"
            },
            "temp_delta_jan_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of January"
            },
            "temp_delta_feb_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of February"
            },
            "temp_delta_mar_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of March"
            },
            "temp_delta_apr_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of April"
            },
            "temp_delta_may_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of May"
            },
            "temp_delta_jun_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of June"
            },
            "temp_delta_jul_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of July"
            },
            "temp_delta_aug_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of August"
            },
            "temp_delta_sep_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of September"
            },
            "temp_delta_oct_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of October"
            },
            "temp_delta_nov_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of November"
            },
            "temp_delta_dec_mean": {
                "type": "number",
                "description": "Difference between the normal high temp and the normal low temp for the month of December"
            },
            "lat": {
                "type": "number",
                "description": "Latitude of the divide (in WGS84 degrees)"
            },
            "lon": {
                "type": "number",
                "description": "Longitude of the divide (in WGS84 degrees)"
            },
            "glacier_percent": {
                "type": "number",
                "description": "Percentage of glacier cover within the divide"
            },
            "cgw": {
                "type": "number",
                "description": "Groundwater Coefficient"
            },
            "expon": {
                "type": "number",
                "description": "Groundwater Exponent"
            },
            "max_gw_storage": {
                "type": "number",
                "description": "The maximum storage capacity (or total height) of the conceptual groundwater bucket"
            },
            "vegetation_height": {
                "type": "number",
                "description": "Vegetation height"
            },
            "zero_plane_displacement_height": {
                "type": "number",
                "description": "Zero-plane displacement height"
            },
            "momentum_transfer_roughness_length": {
                "type": "number",
                "description": "Momentum-transfer roughness length"
            },
            "heat_transfer_roughness_length": {
                "type": "number",
                "description": "Heat-transfer roughness length"
            },
            "surface_longwave_emissivity": {
                "type": "number",
                "description": "Surface longwave emissivity"
            },
            "surface_shortwave_albedo": {
                "type": "number",
                "description": "Surface shortwave albedo"
            },
            "geometry": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": "application/octet-stream",
                "description": "Spatial Geometry (MULTIPOLYGON format) - stored in WKB binary format"
            },
            "gid": {
                "type": "string",
                "description": "Geolocation Plus Code identifier"
            }
        },
        "required": [
            "div_id"
        ]
    }
    ```
