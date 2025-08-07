"""Contains the PyIceberg Table schemas for Hydrofabric v2.2 data model tables"""

import pyarrow as pa
from pyiceberg.schema import Schema
from pyiceberg.types import BinaryType, BooleanType, DoubleType, IntegerType, NestedField, StringType


class DivideAttributes:
    """The schema for divide attributes table

    Attributes
    ----------
    divide_id : str
        Unique divide identifier
    mode.bexp_soil_layers_stag=1 : float
        Beta Parameter: soil C-H B exponent for soil layer 1 (mode)
    mode.bexp_soil_layers_stag=2 : float
        Beta Parameter: soil C-H B exponent for soil layer 2 (mode)
    mode.bexp_soil_layers_stag=3 : float
        Beta Parameter: soil C-H B exponent for soil layer 3 (mode)
    mode.bexp_soil_layers_stag=4 : float
        Beta Parameter: soil C-H B exponent for soil layer 4 (mode)
    mode.ISLTYP : float
        Dominant soil type category (mode)
    mode.IVGTYP : float
        Dominant vegetation type category (mode)
    geom_mean.dksat_soil_layers_stag=1 : float
        Saturated Soil Connectivity for soil layer 1 (geometric mean) [mm/h]
    geom_mean.dksat_soil_layers_stag=2 : float
        Saturated Soil Connectivity for soil layer 2 (geometric mean) [mm/h]
    geom_mean.dksat_soil_layers_stag=3 : float
        Saturated Soil Connectivity for soil layer 3 (geometric mean) [mm/h]
    geom_mean.dksat_soil_layers_stag=4 : float
        Saturated Soil Connectivity for soil layer 4 (geometric mean) [mm/h]
    geom_mean.psisat_soil_layers_stag=1 : float
        Saturated soil matric potential for soil layer 1 (geometric mean) [kPa]
    geom_mean.psisat_soil_layers_stag=2 : float
        Saturated soil matric potential for soil layer 2 (geometric mean) [kPa]
    geom_mean.psisat_soil_layers_stag=3 : float
        Saturated soil matric potential for soil layer 3 (geometric mean) [kPa]
    geom_mean.psisat_soil_layers_stag=4 : float
        Saturated soil matric potential for soil layer 4 (geometric mean) [kPa]
    mean.cwpvt : float
        Empirical canopy wind parameter [1/m]
    mean.mfsno : float
        Snowmelt m parameter (unitless)
    mean.mp : float
        Slope of Conductance to photosynthesis relationship (unitless)
    mean.refkdt : float
        Parameter in the surface runoff parameterization (unitless)
    mean.slope_1km : float
        Slope [0-1] at 1km resolution [degrees]
    mean.smcmax_soil_layers_stag=1 : float
        Saturated value of soil moisture [volumetric] for soil layer 1 [m/m]
    mean.smcmax_soil_layers_stag=2 : float
        Saturated value of soil moisture [volumetric] for soil layer 2 [m/m]
    mean.smcmax_soil_layers_stag=3 : float
        Saturated value of soil moisture [volumetric] for soil layer 3 [m/m]
    mean.smcmax_soil_layers_stag=4 : float
        Saturated value of soil moisture [volumetric] for soil layer 4 [m/m]
    mean.smcwlt_soil_layers_stag=1 : float
        Wilting point soil moisture [volumetric] for soil layer 1 [m/m]
    mean.smcwlt_soil_layers_stag=2 : float
        Wilting point soil moisture [volumetric] for soil layer 2 [m/m]
    mean.smcwlt_soil_layers_stag=3 : float
        Wilting point soil moisture [volumetric] for soil layer 3 [m/m]
    mean.smcwlt_soil_layers_stag=4 : float
        Wilting point soil moisture [volumetric] for soil layer 4 [m/m]
    mean.vcmx25 : float
        Maximum rate of carboxylation at 25 C [μmol/m²/s]
    mean.Coeff : float
        Groundwater Coefficient [m³/s]
    mean.Zmax : float
        The total height of the baseflow "bucket" [mm]
    mode.Expon : float
        Groundwater Exponent (unitless)
    centroid_x : float
        X coordinates of divide centroid [units of CRS]
    centroid_y : float
        Y coordinates of divide centroid [units of CRS]
    mean.impervious : float
        Percent Impervious Surface [percent]
    mean.elevation : float
        Elevation from DEM [meters]
    mean.slope : float
        Slope computed from DEM [0-100] [degrees]
    circ_mean.aspect : float
        Aspect computed from DEM [degrees]
    dist_4.twi : str
        Topographic Wetness Index quartile distribution (unitless)
    vpuid : str
        Vector Processing Unit ID
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "divide_id",
            "mode.bexp_soil_layers_stag=1",
            "mode.bexp_soil_layers_stag=2",
            "mode.bexp_soil_layers_stag=3",
            "mode.bexp_soil_layers_stag=4",
            "mode.ISLTYP",
            "mode.IVGTYP",
            "geom_mean.dksat_soil_layers_stag=1",
            "geom_mean.dksat_soil_layers_stag=2",
            "geom_mean.dksat_soil_layers_stag=3",
            "geom_mean.dksat_soil_layers_stag=4",
            "geom_mean.psisat_soil_layers_stag=1",
            "geom_mean.psisat_soil_layers_stag=2",
            "geom_mean.psisat_soil_layers_stag=3",
            "geom_mean.psisat_soil_layers_stag=4",
            "mean.cwpvt",
            "mean.mfsno",
            "mean.mp",
            "mean.refkdt",
            "mean.slope_1km",
            "mean.smcmax_soil_layers_stag=1",
            "mean.smcmax_soil_layers_stag=2",
            "mean.smcmax_soil_layers_stag=3",
            "mean.smcmax_soil_layers_stag=4",
            "mean.smcwlt_soil_layers_stag=1",
            "mean.smcwlt_soil_layers_stag=2",
            "mean.smcwlt_soil_layers_stag=3",
            "mean.smcwlt_soil_layers_stag=4",
            "mean.vcmx25",
            "mean.Coeff",
            "mean.Zmax",
            "mode.Expon",
            "centroid_x",
            "centroid_y",
            "mean.impervious",
            "mean.elevation",
            "mean.slope",
            "circ_mean.aspect",
            "dist_4.twi",
            "vpuid",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for divide attributes table
        """
        return Schema(
            NestedField(1, "divide_id", StringType(), required=True),
            NestedField(2, "mode.bexp_soil_layers_stag=1", DoubleType(), required=False),
            NestedField(3, "mode.bexp_soil_layers_stag=2", DoubleType(), required=False),
            NestedField(4, "mode.bexp_soil_layers_stag=3", DoubleType(), required=False),
            NestedField(5, "mode.bexp_soil_layers_stag=4", DoubleType(), required=False),
            NestedField(6, "mode.ISLTYP", DoubleType(), required=False),
            NestedField(7, "mode.IVGTYP", DoubleType(), required=False),
            NestedField(8, "geom_mean.dksat_soil_layers_stag=1", DoubleType(), required=False),
            NestedField(9, "geom_mean.dksat_soil_layers_stag=2", DoubleType(), required=False),
            NestedField(10, "geom_mean.dksat_soil_layers_stag=3", DoubleType(), required=False),
            NestedField(11, "geom_mean.dksat_soil_layers_stag=4", DoubleType(), required=False),
            NestedField(12, "geom_mean.psisat_soil_layers_stag=1", DoubleType(), required=False),
            NestedField(13, "geom_mean.psisat_soil_layers_stag=2", DoubleType(), required=False),
            NestedField(14, "geom_mean.psisat_soil_layers_stag=3", DoubleType(), required=False),
            NestedField(15, "geom_mean.psisat_soil_layers_stag=4", DoubleType(), required=False),
            NestedField(16, "mean.cwpvt", DoubleType(), required=False),
            NestedField(17, "mean.mfsno", DoubleType(), required=False),
            NestedField(18, "mean.mp", DoubleType(), required=False),
            NestedField(19, "mean.refkdt", DoubleType(), required=False),
            NestedField(20, "mean.slope_1km", DoubleType(), required=False),
            NestedField(21, "mean.smcmax_soil_layers_stag=1", DoubleType(), required=False),
            NestedField(22, "mean.smcmax_soil_layers_stag=2", DoubleType(), required=False),
            NestedField(23, "mean.smcmax_soil_layers_stag=3", DoubleType(), required=False),
            NestedField(24, "mean.smcmax_soil_layers_stag=4", DoubleType(), required=False),
            NestedField(25, "mean.smcwlt_soil_layers_stag=1", DoubleType(), required=False),
            NestedField(26, "mean.smcwlt_soil_layers_stag=2", DoubleType(), required=False),
            NestedField(27, "mean.smcwlt_soil_layers_stag=3", DoubleType(), required=False),
            NestedField(28, "mean.smcwlt_soil_layers_stag=4", DoubleType(), required=False),
            NestedField(29, "mean.vcmx25", DoubleType(), required=False),
            NestedField(30, "mean.Coeff", DoubleType(), required=False),
            NestedField(31, "mean.Zmax", DoubleType(), required=False),
            NestedField(32, "mode.Expon", DoubleType(), required=False),
            NestedField(33, "centroid_x", DoubleType(), required=False),
            NestedField(34, "centroid_y", DoubleType(), required=False),
            NestedField(35, "mean.impervious", DoubleType(), required=False),
            NestedField(36, "mean.elevation", DoubleType(), required=False),
            NestedField(37, "mean.slope", DoubleType(), required=False),
            NestedField(38, "circ_mean.aspect", DoubleType(), required=False),
            NestedField(39, "dist_4.twi", StringType(), required=False),
            NestedField(40, "vpuid", StringType(), required=True),
            identifier_field_ids=[1, 40],
        )

    @classmethod
    def arrow_schema(cls):
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for divide attributes table
        """
        fields = [
            pa.field("divide_id", pa.string(), nullable=False),
            pa.field("mode.bexp_soil_layers_stag=1", pa.float64()),
            pa.field("mode.bexp_soil_layers_stag=2", pa.float64()),
            pa.field("mode.bexp_soil_layers_stag=3", pa.float64()),
            pa.field("mode.bexp_soil_layers_stag=4", pa.float64()),
            pa.field("mode.ISLTYP", pa.float64()),
            pa.field("mode.IVGTYP", pa.float64()),
            pa.field("geom_mean.dksat_soil_layers_stag=1", pa.float64()),
            pa.field("geom_mean.dksat_soil_layers_stag=2", pa.float64()),
            pa.field("geom_mean.dksat_soil_layers_stag=3", pa.float64()),
            pa.field("geom_mean.dksat_soil_layers_stag=4", pa.float64()),
            pa.field("geom_mean.psisat_soil_layers_stag=1", pa.float64()),
            pa.field("geom_mean.psisat_soil_layers_stag=2", pa.float64()),
            pa.field("geom_mean.psisat_soil_layers_stag=3", pa.float64()),
            pa.field("geom_mean.psisat_soil_layers_stag=4", pa.float64()),
            pa.field("mean.cwpvt", pa.float64()),
            pa.field("mean.mfsno", pa.float64()),
            pa.field("mean.mp", pa.float64()),
            pa.field("mean.refkdt", pa.float64()),
            pa.field("mean.slope_1km", pa.float64()),
            pa.field("mean.smcmax_soil_layers_stag=1", pa.float64()),
            pa.field("mean.smcmax_soil_layers_stag=2", pa.float64()),
            pa.field("mean.smcmax_soil_layers_stag=3", pa.float64()),
            pa.field("mean.smcmax_soil_layers_stag=4", pa.float64()),
            pa.field("mean.smcwlt_soil_layers_stag=1", pa.float64()),
            pa.field("mean.smcwlt_soil_layers_stag=2", pa.float64()),
            pa.field("mean.smcwlt_soil_layers_stag=3", pa.float64()),
            pa.field("mean.smcwlt_soil_layers_stag=4", pa.float64()),
            pa.field("mean.vcmx25", pa.float64()),
            pa.field("mean.Coeff", pa.float64()),
            pa.field("mean.Zmax", pa.float64()),
            pa.field("mode.Expon", pa.float64()),
            pa.field("centroid_x", pa.float64()),
            pa.field("centroid_y", pa.float64()),
            pa.field("mean.impervious", pa.float64()),
            pa.field("mean.elevation", pa.float64()),
            pa.field("mean.slope", pa.float64()),
            pa.field("circ_mean.aspect", pa.float64()),
            pa.field("dist_4.twi", pa.string()),
            pa.field("vpuid", pa.string(), nullable=False),
        ]

        return pa.schema(fields)


class Divides:
    """The schema for divides table

    Attributes
    ----------
    divide_id : str
        Unique divide identifier
    toid : str
        Flowpath id where water flows
    type : str
        Divide Type, one of coastal, internal, network
    ds_id : float
        Most Downstream flowpath element adjacent to internal divides
    areasqkm : float
        Incremental Areas of Divide [square kilometers]
    vpuid : str
        Vector Processing Unit ID
    id : str
        Unique flowpath identifier
    lengthkm : float
        Length in kilometers of Flowpath
    tot_drainage_areasqkm : float
        Total Upstream Drainage Area [square kilometers]
    has_flowline : bool
        Does divide have an associated flowpath
    geometry : binary
        Spatial Geometry (POLYGON format)
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "divide_id",
            "toid",
            "type",
            "ds_id",
            "areasqkm",
            "vpuid",
            "id",
            "lengthkm",
            "tot_drainage_areasqkm",
            "has_flowline",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for divides table
        """
        return Schema(
            NestedField(1, "divide_id", StringType(), required=True),
            NestedField(2, "toid", StringType(), required=False),
            NestedField(3, "type", StringType(), required=False),
            NestedField(4, "ds_id", DoubleType(), required=False),
            NestedField(5, "areasqkm", DoubleType(), required=False),
            NestedField(6, "vpuid", StringType(), required=True),
            NestedField(7, "id", StringType(), required=False),
            NestedField(8, "lengthkm", DoubleType(), required=False),
            NestedField(9, "tot_drainage_areasqkm", DoubleType(), required=False),
            NestedField(10, "has_flowline", BooleanType(), required=False),
            NestedField(11, "geometry", BinaryType(), required=False),
            identifier_field_ids=[1, 6],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for divides table
        """
        return pa.schema(
            [
                pa.field("divide_id", pa.string(), nullable=False),
                pa.field("toid", pa.string(), nullable=True),
                pa.field("type", pa.string(), nullable=True),
                pa.field("ds_id", pa.float64(), nullable=True),
                pa.field("areasqkm", pa.float64(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=False),
                pa.field("id", pa.string(), nullable=True),
                pa.field("lengthkm", pa.float64(), nullable=True),
                pa.field("tot_drainage_areasqkm", pa.float64(), nullable=True),
                pa.field("has_flowline", pa.bool_(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class FlowpathAttributes:
    """The schema for flowpath attributes table

    Attributes
    ----------
    link : str
        Identical to id, but naming needed for t-route
    to : str
        Identical to toid, but naming needed for t-route
    Length_m : float
        Length of flowpath id [meters]
    Y : float
        Estimated depth (m) associated with TopWdth
    n : float
        Manning's in channel roughness
    nCC : float
        Compound Channel Manning's roughness
    BtmWdth : float
        Bottom width of channel [meters]
    TopWdth : float
        Top Width [meters]
    TopWdthCC : float
        Compound Channel Top Width [meters]
    ChSlp : float
        Channel side slope
    alt : float
        Elevation in meters, at the headwater node, taken from the 3DEP 10m DEM
    So : float
        Slope [meters/meters], computed from the 3DEP 10m DEM
    MusX : float
        Muskingum routing parameter
    MusK : float
        Muskingum routing time [seconds]
    gage : str
        If there is a gage, the hl_link is stored
    gage_nex_id : str
        The downstream nexus associated with the gage
    WaterbodyID : str
        If there is a waterbody, the hl_link is stored
    waterbody_nex_id : str
        The downstream nexus associated with the waterbody
    id : str
        Unique flowpath identifier
    toid : str
        Flowpath id where water flows
    vpuid : str
        Vector Processing Unit ID
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "link",
            "to",
            "Length_m",
            "Y",
            "n",
            "nCC",
            "BtmWdth",
            "TopWdth",
            "TopWdthCC",
            "ChSlp",
            "alt",
            "So",
            "MusX",
            "MusK",
            "gage",
            "gage_nex_id",
            "WaterbodyID",
            "waterbody_nex_id",
            "id",
            "toid",
            "vpuid",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for flowpath attributes table
        """
        return Schema(
            NestedField(1, "link", StringType(), required=False),
            NestedField(2, "to", StringType(), required=False),
            NestedField(3, "Length_m", DoubleType(), required=False),
            NestedField(4, "Y", DoubleType(), required=False),
            NestedField(5, "n", DoubleType(), required=False),
            NestedField(6, "nCC", DoubleType(), required=False),
            NestedField(7, "BtmWdth", DoubleType(), required=False),
            NestedField(8, "TopWdth", DoubleType(), required=False),
            NestedField(9, "TopWdthCC", DoubleType(), required=False),
            NestedField(10, "ChSlp", DoubleType(), required=False),
            NestedField(11, "alt", DoubleType(), required=False),
            NestedField(12, "So", DoubleType(), required=False),
            NestedField(13, "MusX", DoubleType(), required=False),
            NestedField(14, "MusK", DoubleType(), required=False),
            NestedField(15, "gage", StringType(), required=False),
            NestedField(16, "gage_nex_id", StringType(), required=False),
            NestedField(17, "WaterbodyID", StringType(), required=False),
            NestedField(18, "waterbody_nex_id", StringType(), required=False),
            NestedField(19, "id", StringType(), required=True),
            NestedField(20, "toid", StringType(), required=True),
            NestedField(21, "vpuid", StringType(), required=True),
            identifier_field_ids=[19, 20, 21],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for flowpath attributes table
        """
        return pa.schema(
            [
                pa.field("link", pa.string(), nullable=True),
                pa.field("to", pa.string(), nullable=True),
                pa.field("Length_m", pa.float64(), nullable=True),
                pa.field("Y", pa.float64(), nullable=True),
                pa.field("n", pa.float64(), nullable=True),
                pa.field("nCC", pa.float64(), nullable=True),
                pa.field("BtmWdth", pa.float64(), nullable=True),
                pa.field("TopWdth", pa.float64(), nullable=True),
                pa.field("TopWdthCC", pa.float64(), nullable=True),
                pa.field("ChSlp", pa.float64(), nullable=True),
                pa.field("alt", pa.float64(), nullable=True),
                pa.field("So", pa.float64(), nullable=True),
                pa.field("MusX", pa.float64(), nullable=True),
                pa.field("MusK", pa.float64(), nullable=True),
                pa.field("gage", pa.string(), nullable=True),
                pa.field("gage_nex_id", pa.string(), nullable=True),
                pa.field("WaterbodyID", pa.string(), nullable=True),
                pa.field("waterbody_nex_id", pa.string(), nullable=True),
                pa.field("id", pa.string(), nullable=False),
                pa.field("toid", pa.string(), nullable=False),
                pa.field("vpuid", pa.string(), nullable=False),
            ]
        )


class FlowpathAttributesML:
    """The schema for machine learning flowpath attributes table

    Attributes
    ----------
    link : str
        Identical to id, but naming needed for t-route
    to : str
        Identical to toid, but naming needed for t-route
    Length_m : float
        Length of flowpath id [meters]
    alt : float
        Elevation in meters, at the headwater node, taken from the 3DEP 10m DEM
    So : float
        Slope [meters/meters], computed from the 3DEP 10m DEM
    MusX : float
        Muskingum routing parameter
    MusK : float
        Muskingum routing time [seconds]
    gage : str
        If there is a gage, the hl_link is stored
    gage_nex_id : str
        The downstream nexus associated with the gage
    WaterbodyID : str
        If there is a waterbody, the hl_link is stored
    waterbody_nex_id : str
        The downstream nexus associated with the waterbody
    id : str
        Unique flowpath identifier
    toid : str
        Flowpath id where water flows
    vpuid : str
        Vector Processing Unit ID
    n : float
        Manning's in channel roughness
    BtmWdth : float
        Bottom width of channel [meters]
    TopWdth : float
        Top Width [meters]
    ChSlp : float
        Channel side slope
    nCC : float
        Compound Channel Manning's roughness
    TopWdthCC : float
        Compound Channel Top Width [meters]
    Y : float
        Estimated depth (m) associated with TopWdth
    YCC : float
        Estimated depth (m) associated with TopWdthCC
    dingman_r : float
        Estimated channel shape parameter
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "link",
            "to",
            "Length_m",
            "alt",
            "So",
            "MusX",
            "MusK",
            "gage",
            "gage_nex_id",
            "WaterbodyID",
            "waterbody_nex_id",
            "id",
            "toid",
            "vpuid",
            "n",
            "BtmWdth",
            "TopWdth",
            "ChSlp",
            "nCC",
            "TopWdthCC",
            "Y",
            "YCC",
            "dingman_r",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for flowpath attributes ML table
        """
        return Schema(
            NestedField(1, "link", StringType(), required=False),
            NestedField(2, "to", StringType(), required=False),
            NestedField(3, "Length_m", DoubleType(), required=False),
            NestedField(4, "alt", DoubleType(), required=False),
            NestedField(5, "So", DoubleType(), required=False),
            NestedField(6, "MusX", DoubleType(), required=False),
            NestedField(7, "MusK", DoubleType(), required=False),
            NestedField(8, "gage", StringType(), required=False),
            NestedField(9, "gage_nex_id", StringType(), required=False),
            NestedField(10, "WaterbodyID", StringType(), required=False),
            NestedField(11, "waterbody_nex_id", StringType(), required=False),
            NestedField(12, "id", StringType(), required=True),
            NestedField(13, "toid", StringType(), required=True),
            NestedField(14, "vpuid", StringType(), required=True),
            NestedField(15, "n", DoubleType(), required=False),
            NestedField(16, "BtmWdth", DoubleType(), required=False),
            NestedField(17, "TopWdth", DoubleType(), required=False),
            NestedField(18, "ChSlp", DoubleType(), required=False),
            NestedField(19, "nCC", DoubleType(), required=False),
            NestedField(20, "TopWdthCC", DoubleType(), required=False),
            NestedField(21, "Y", DoubleType(), required=False),
            NestedField(22, "YCC", DoubleType(), required=False),
            NestedField(23, "dingman_r", DoubleType(), required=False),
            identifier_field_ids=[12, 13, 14],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for flowpath attributes ML table
        """
        return pa.schema(
            [
                pa.field("link", pa.string(), nullable=True),
                pa.field("to", pa.string(), nullable=True),
                pa.field("Length_m", pa.float64(), nullable=True),
                pa.field("alt", pa.float64(), nullable=True),
                pa.field("So", pa.float64(), nullable=True),
                pa.field("MusX", pa.float64(), nullable=True),
                pa.field("MusK", pa.float64(), nullable=True),
                pa.field("gage", pa.string(), nullable=True),
                pa.field("gage_nex_id", pa.string(), nullable=True),
                pa.field("WaterbodyID", pa.string(), nullable=True),
                pa.field("waterbody_nex_id", pa.string(), nullable=True),
                pa.field("id", pa.string(), nullable=False),
                pa.field("toid", pa.string(), nullable=False),
                pa.field("vpuid", pa.string(), nullable=False),
                pa.field("n", pa.float64(), nullable=True),
                pa.field("BtmWdth", pa.float64(), nullable=True),
                pa.field("TopWdth", pa.float64(), nullable=True),
                pa.field("ChSlp", pa.float64(), nullable=True),
                pa.field("nCC", pa.float64(), nullable=True),
                pa.field("TopWdthCC", pa.float64(), nullable=True),
                pa.field("Y", pa.float64(), nullable=True),
                pa.field("YCC", pa.float64(), nullable=True),
                pa.field("dingman_r", pa.float64(), nullable=True),
            ]
        )


class Flowpaths:
    """The schema for flowpaths table

    Attributes
    ----------
    id : str
        Unique flowpath identifier
    toid : str
        Flowpath id where water flows
    mainstem : float
        Persistent Mainstem Identifier
    order : float
        Stream order (Strahler)
    hydroseq : int
        Hydrologic Sequence
    lengthkm : float
        Length in kilometers of Flowpath
    areasqkm : float
        Incremental Areas of Divide [square kilometers]
    tot_drainage_areasqkm : float
        Total Upstream Drainage Area [square kilometers]
    has_divide : bool
        Does Flowpath ID have an associated divide
    divide_id : str
        Unique divide identifier
    poi_id : str
        Unique Point of Interest identifier
    vpuid : str
        Vector Processing Unit ID
    geometry : binary
        Spatial Geometry (LINESTRING format)
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "id",
            "toid",
            "mainstem",
            "order",
            "hydroseq",
            "lengthkm",
            "areasqkm",
            "tot_drainage_areasqkm",
            "has_divide",
            "divide_id",
            "poi_id",
            "vpuid",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for flowpaths table
        """
        return Schema(
            NestedField(1, "id", StringType(), required=True),
            NestedField(2, "toid", StringType(), required=True),
            NestedField(3, "mainstem", DoubleType(), required=False),
            NestedField(4, "order", DoubleType(), required=False),
            NestedField(5, "hydroseq", IntegerType(), required=False),
            NestedField(6, "lengthkm", DoubleType(), required=False),
            NestedField(7, "areasqkm", DoubleType(), required=False),
            NestedField(8, "tot_drainage_areasqkm", DoubleType(), required=False),
            NestedField(9, "has_divide", BooleanType(), required=False),
            NestedField(10, "divide_id", StringType(), required=True),
            NestedField(11, "poi_id", StringType(), required=False),
            NestedField(12, "vpuid", StringType(), required=True),
            NestedField(13, "geometry", BinaryType(), required=False),
            identifier_field_ids=[1, 2, 10, 12],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for flowpaths table
        """
        return pa.schema(
            [
                pa.field("id", pa.string(), nullable=False),
                pa.field("toid", pa.string(), nullable=False),
                pa.field("mainstem", pa.float64(), nullable=True),
                pa.field("order", pa.float64(), nullable=True),
                pa.field("hydroseq", pa.int32(), nullable=True),
                pa.field("lengthkm", pa.float64(), nullable=True),
                pa.field("areasqkm", pa.float64(), nullable=True),
                pa.field("tot_drainage_areasqkm", pa.float64(), nullable=True),
                pa.field("has_divide", pa.bool_(), nullable=True),
                pa.field("divide_id", pa.string(), nullable=False),
                pa.field("poi_id", pa.string(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=False),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Hydrolocations:
    """The schema for hydrolocations table

    Attributes
    ----------
    poi_id : int
        Unique Point of Interest identifier
    id : str
        Unique flowpath identifier
    nex_id : str
        Unique nexus ID
    hf_id : float
        Unique ID of the source (hf_source) reference hydrofabric
    hl_link : str
        Unique ID of the hydrolocations in the reference dataset
    hl_reference : str
        Native dataset that hydrolocation was extracted from
    hl_uri : str
        Concatenation of hl_reference and hl_link
    hl_source : str
        Where is the data source from? USGS-NOAA Reference Fabric, or, NOAA-OWP
    hl_x : float
        X coordinate of the hydrolocation
    hl_y : float
        Y coordinate of the hydrolocation
    vpuid : str
        Vector Processing Unit ID
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "poi_id",
            "id",
            "nex_id",
            "hf_id",
            "hl_link",
            "hl_reference",
            "hl_uri",
            "hl_source",
            "hl_x",
            "hl_y",
            "vpuid",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for hydrolocations table
        """
        return Schema(
            NestedField(1, "poi_id", IntegerType(), required=False),
            NestedField(2, "id", StringType(), required=True),
            NestedField(3, "nex_id", StringType(), required=True),
            NestedField(4, "hf_id", DoubleType(), required=False),
            NestedField(5, "hl_link", StringType(), required=False),
            NestedField(6, "hl_reference", StringType(), required=False),
            NestedField(7, "hl_uri", StringType(), required=False),
            NestedField(8, "hl_source", StringType(), required=False),
            NestedField(9, "hl_x", DoubleType(), required=False),
            NestedField(10, "hl_y", DoubleType(), required=False),
            NestedField(11, "vpuid", StringType(), required=True),
            identifier_field_ids=[2, 3, 11],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for hydrolocations table
        """
        return pa.schema(
            [
                pa.field("poi_id", pa.int32(), nullable=True),
                pa.field("id", pa.string(), nullable=False),
                pa.field("nex_id", pa.string(), nullable=False),
                pa.field("hf_id", pa.float64(), nullable=True),
                pa.field("hl_link", pa.string(), nullable=True),
                pa.field("hl_reference", pa.string(), nullable=True),
                pa.field("hl_uri", pa.string(), nullable=True),
                pa.field("hl_source", pa.string(), nullable=True),
                pa.field("hl_x", pa.float64(), nullable=True),
                pa.field("hl_y", pa.float64(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=False),
            ]
        )


class Lakes:
    """The schema for lakes table

    Attributes
    ----------
    lake_id : float
        Unique NWS Lake ID (taken from NHDPlus)
    LkArea : float
        Area associated with lake_id [square kilometers]
    LkMxE : float
        Maximum lake elevation [meters above sea level]
    WeirC : float
        Weir coefficient
    WeirL : float
        Weir length [meters]
    OrificeC : float
        Orifice coefficient
    OrificeA : float
        Orifice cross-sectional area [square meters]
    OrificeE : float
        Orifice elevation [meters above sea level]
    WeirE : float
        Weir elevation [meters above sea level]
    ifd : float
        Initial fraction water depth
    Dam_Length : float
        Length of the dam in meters
    domain : str
        Domain of Hydrofabric (conus, hi, gl, ak, prvi)
    poi_id : int
        Unique Point of Interest identifier
    hf_id : float
        Unique ID of the source (hf_source) reference hydrofabric
    reservoir_index_AnA : float
        Reservoir release data type for AnA configuration; Level pool = 1, USGS-persistence = 2, USACE-persistence = 3, RFC-forecasts = 4
    reservoir_index_Extended_AnA : float
        Reservoir release data type for extended AnA configuration; Level pool = 1, USGS-persistence = 2, USACE-persistence = 3, RFC-forecasts = 4
    reservoir_index_GDL_AK : float
        Reservoir release data type for Alaska domain; Level pool = 1, USGS-persistence = 2, USACE-persistence = 3, RFC-forecasts = 4, APRFC-GDL = 5
    reservoir_index_Medium_Range : float
        Reservoir release data type for extended medium range configuration; Level pool = 1, USGS-persistence = 2, USACE-persistence = 3, RFC-forecasts = 4
    reservoir_index_Short_Range : float
        Reservoir release data type for extended short range configuration; Level pool = 1, USGS-persistence = 2, USACE-persistence = 3, RFC-forecasts = 4
    res_id : str
        Unique Reservoir Identifier
    vpuid : str
        Vector Processing Unit ID
    lake_x : float
        X coordinate of the lake centroid
    lake_y : float
        Y coordinate of the lake centroid
    geometry : binary
        Spatial Geometry (POLYGON format)
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "lake_id",
            "LkArea",
            "LkMxE",
            "WeirC",
            "WeirL",
            "OrificeC",
            "OrificeA",
            "OrificeE",
            "WeirE",
            "ifd",
            "Dam_Length",
            "domain",
            "poi_id",
            "hf_id",
            "reservoir_index_AnA",
            "reservoir_index_Extended_AnA",
            "reservoir_index_GDL_AK",
            "reservoir_index_Medium_Range",
            "reservoir_index_Short_Range",
            "res_id",
            "vpuid",
            "lake_x",
            "lake_y",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for lakes table
        """
        return Schema(
            NestedField(1, "lake_id", DoubleType(), required=False),
            NestedField(2, "LkArea", DoubleType(), required=False),
            NestedField(3, "LkMxE", DoubleType(), required=False),
            NestedField(4, "WeirC", DoubleType(), required=False),
            NestedField(5, "WeirL", DoubleType(), required=False),
            NestedField(6, "OrificeC", DoubleType(), required=False),
            NestedField(7, "OrificeA", DoubleType(), required=False),
            NestedField(8, "OrificeE", DoubleType(), required=False),
            NestedField(9, "WeirE", DoubleType(), required=False),
            NestedField(10, "ifd", DoubleType(), required=False),
            NestedField(11, "Dam_Length", DoubleType(), required=False),
            NestedField(12, "domain", StringType(), required=False),
            NestedField(13, "poi_id", IntegerType(), required=True),
            NestedField(14, "hf_id", DoubleType(), required=False),
            NestedField(15, "reservoir_index_AnA", DoubleType(), required=False),
            NestedField(16, "reservoir_index_Extended_AnA", DoubleType(), required=False),
            NestedField(17, "reservoir_index_GDL_AK", DoubleType(), required=False),
            NestedField(18, "reservoir_index_Medium_Range", DoubleType(), required=False),
            NestedField(19, "reservoir_index_Short_Range", DoubleType(), required=False),
            NestedField(20, "res_id", StringType(), required=False),
            NestedField(21, "vpuid", StringType(), required=True),
            NestedField(22, "lake_x", DoubleType(), required=False),
            NestedField(23, "lake_y", DoubleType(), required=False),
            NestedField(24, "geometry", BinaryType(), required=False),
            identifier_field_ids=[13, 21],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for lakes table
        """
        return pa.schema(
            [
                pa.field("lake_id", pa.float64(), nullable=True),
                pa.field("LkArea", pa.float64(), nullable=True),
                pa.field("LkMxE", pa.float64(), nullable=True),
                pa.field("WeirC", pa.float64(), nullable=True),
                pa.field("WeirL", pa.float64(), nullable=True),
                pa.field("OrificeC", pa.float64(), nullable=True),
                pa.field("OrificeA", pa.float64(), nullable=True),
                pa.field("OrificeE", pa.float64(), nullable=True),
                pa.field("WeirE", pa.float64(), nullable=True),
                pa.field("ifd", pa.float64(), nullable=True),
                pa.field("Dam_Length", pa.float64(), nullable=True),
                pa.field("domain", pa.string(), nullable=True),
                pa.field("poi_id", pa.int32(), nullable=False),
                pa.field("hf_id", pa.float64(), nullable=True),
                pa.field("reservoir_index_AnA", pa.float64(), nullable=True),
                pa.field("reservoir_index_Extended_AnA", pa.float64(), nullable=True),
                pa.field("reservoir_index_GDL_AK", pa.float64(), nullable=True),
                pa.field("reservoir_index_Medium_Range", pa.float64(), nullable=True),
                pa.field("reservoir_index_Short_Range", pa.float64(), nullable=True),
                pa.field("res_id", pa.string(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=False),
                pa.field("lake_x", pa.float64(), nullable=True),
                pa.field("lake_y", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class Network:
    """The schema for network table

    Attributes
    ----------
    id : str
        Unique flowpath identifier
    toid : str
        Flowpath id where water flows
    divide_id : str
        Unique divide identifier
    ds_id : float
        Most Downstream flowpath element adjacent to internal divides
    mainstem : float
        Persistent Mainstem Identifier
    hydroseq : float
        Hydrologic Sequence
    hf_source : str
        Source of the reference hydrofabric
    hf_id : float
        Unique ID of the source (hf_source) reference hydrofabric
    lengthkm : float
        Length in kilometers of Flowpath
    areasqkm : float
        Incremental Areas of Divide [square kilometers]
    tot_drainage_areasqkm : float
        Total Upstream Drainage Area [square kilometers]
    type : str
        Feature type, one of coastal, internal, network
    vpuid : str
        Vector Processing Unit ID
    hf_hydroseq : float
        Source hydrofabric hydrosequence
    hf_lengthkm : float
        Source hydrofabric length in kilometers
    hf_mainstem : float
        Source hydrofabric mainstem
    topo : str
        Topological information
    poi_id : float
        Unique Point of Interest identifier
    hl_uri : str
        Concatenation of hl_reference and hl_link
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "id",
            "toid",
            "divide_id",
            "ds_id",
            "mainstem",
            "hydroseq",
            "hf_source",
            "hf_id",
            "lengthkm",
            "areasqkm",
            "tot_drainage_areasqkm",
            "type",
            "vpuid",
            "hf_hydroseq",
            "hf_lengthkm",
            "hf_mainstem",
            "topo",
            "poi_id",
            "hl_uri",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for network table
        """
        return Schema(
            NestedField(1, "id", StringType(), required=False),
            NestedField(2, "toid", StringType(), required=False),
            NestedField(3, "divide_id", StringType(), required=False),
            NestedField(4, "ds_id", DoubleType(), required=False),
            NestedField(5, "mainstem", DoubleType(), required=False),
            NestedField(6, "hydroseq", DoubleType(), required=False),
            NestedField(7, "hf_source", StringType(), required=False),
            NestedField(8, "hf_id", DoubleType(), required=False),
            NestedField(9, "lengthkm", DoubleType(), required=False),
            NestedField(10, "areasqkm", DoubleType(), required=False),
            NestedField(11, "tot_drainage_areasqkm", DoubleType(), required=False),
            NestedField(12, "type", StringType(), required=False),
            NestedField(13, "vpuid", StringType(), required=False),
            NestedField(14, "hf_hydroseq", DoubleType(), required=False),
            NestedField(15, "hf_lengthkm", DoubleType(), required=False),
            NestedField(16, "hf_mainstem", DoubleType(), required=False),
            NestedField(17, "topo", StringType(), required=False),
            NestedField(18, "poi_id", DoubleType(), required=False),
            NestedField(19, "hl_uri", StringType(), required=False),
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for network table
        """
        return pa.schema(
            [
                pa.field("id", pa.string(), nullable=True),
                pa.field("toid", pa.string(), nullable=True),
                pa.field("divide_id", pa.string(), nullable=True),
                pa.field("ds_id", pa.float64(), nullable=True),
                pa.field("mainstem", pa.float64(), nullable=True),
                pa.field("hydroseq", pa.float64(), nullable=True),
                pa.field("hf_source", pa.string(), nullable=True),
                pa.field("hf_id", pa.float64(), nullable=True),
                pa.field("lengthkm", pa.float64(), nullable=True),
                pa.field("areasqkm", pa.float64(), nullable=True),
                pa.field("tot_drainage_areasqkm", pa.float64(), nullable=True),
                pa.field("type", pa.string(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=True),
                pa.field("hf_hydroseq", pa.float64(), nullable=True),
                pa.field("hf_lengthkm", pa.float64(), nullable=True),
                pa.field("hf_mainstem", pa.float64(), nullable=True),
                pa.field("topo", pa.string(), nullable=True),
                pa.field("poi_id", pa.float64(), nullable=True),
                pa.field("hl_uri", pa.string(), nullable=True),
            ]
        )


class Nexus:
    """The schema for nexus table

    Attributes
    ----------
    id : str
        Unique flowpath identifier
    toid : str
        Flowpath id where water flows
    type : str
        Nexus type, one of coastal, internal, network
    vpuid : str
        Vector Processing Unit ID
    poi_id : float
        Unique Point of Interest identifier
    geometry : binary
        Spatial Geometry (POINT format)
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "id",
            "toid",
            "type",
            "vpuid",
            "poi_id",
            "geometry",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for nexus table
        """
        return Schema(
            NestedField(1, "id", StringType(), required=True),
            NestedField(2, "toid", StringType(), required=True),
            NestedField(3, "type", StringType(), required=False),
            NestedField(4, "vpuid", StringType(), required=True),
            NestedField(5, "poi_id", DoubleType(), required=False),
            NestedField(6, "geometry", BinaryType(), required=False),
            identifier_field_ids=[1, 2, 4],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for nexus table
        """
        return pa.schema(
            [
                pa.field("id", pa.string(), nullable=False),
                pa.field("toid", pa.string(), nullable=False),
                pa.field("type", pa.string(), nullable=True),
                pa.field("vpuid", pa.string(), nullable=False),
                pa.field("poi_id", pa.float64(), nullable=True),
                pa.field("geometry", pa.binary(), nullable=True),
            ]
        )


class POIs:
    """The schema for points of interest (POIs) table

    Attributes
    ----------
    poi_id : int
        Unique Point of Interest identifier
    id : str
        Unique flowpath identifier
    nex_id : str
        Unique nexus ID
    vpuid : str
        Vector Processing Unit ID
    """

    @classmethod
    def columns(cls) -> list[str]:
        """Returns the columns associated with this schema

        Returns
        -------
        list[str]
            The schema columns
        """
        return [
            "poi_id",
            "id",
            "nex_id",
            "vpuid",
        ]

    @classmethod
    def schema(cls) -> Schema:
        """Returns the PyIceberg Schema object.

        Returns
        -------
        Schema
            PyIceberg schema for POIs table
        """
        return Schema(
            NestedField(1, "poi_id", IntegerType(), required=True),
            NestedField(2, "id", StringType(), required=True),
            NestedField(3, "nex_id", StringType(), required=True),
            NestedField(4, "vpuid", StringType(), required=True),
            identifier_field_ids=[1, 2, 3, 4],
        )

    @classmethod
    def arrow_schema(cls) -> pa.Schema:
        """Returns the PyArrow Schema object.

        Returns
        -------
        pa.Schema
            PyArrow schema for POIs table
        """
        return pa.schema(
            [
                pa.field("poi_id", pa.int32(), nullable=False),
                pa.field("id", pa.string(), nullable=False),
                pa.field("nex_id", pa.string(), nullable=False),
                pa.field("vpuid", pa.string(), nullable=False),
            ]
        )
