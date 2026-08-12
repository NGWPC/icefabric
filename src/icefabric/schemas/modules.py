"""A file to host schemas for all NWM modules. Based off the table from https://confluence.nextgenwaterprediction.com/pages/viewpage.action?spaceKey=NGWPC&title=BMI+Exchange+Items+and+Module+Parameters"""

import enum
from pathlib import Path
from typing import ClassVar, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class FloatWithUnits(BaseModel):
    """Pydantic class to represent a parameter's float value and units"""

    value: float | None
    units: str | None


class FloatListWithUnits(BaseModel):
    """Pydantic class to represent a list of float values and a single units field"""

    value: list[float]
    units: str | None


class NWMProtocol(Protocol):
    """Protocol defining the interface that configuration NWM BaseModel classes should implement."""

    def to_bmi_config(self) -> list[str]:
        """Converts the contents of the base class to a BMI config for that specific module"""
        ...

    def model_dump_config(self, output_path: Path) -> Path:  # Changed to return Path
        """Outputs the BaseModel to a BMI Config file"""
        ...


class IceFractionScheme(enum.Enum):
    """The ice fraction scheme to be used in SFT"""

    SCHAAKE = "Schaake"
    XINANJIANG = "Xinanjiang"


class SFT(BaseModel):
    """Pydantic model for SFT (Snow Freeze Thaw) module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    soil_moisture_bmi: int = Field(default=1, description="Soil moisture BMI parameter")
    soil_params_smcmax: FloatWithUnits = Field(
        ...,
        description="Maximum soil moisture content",
        alias="smcmax",
        serialization_alias="smcmax",
    )
    soil_params_b: FloatWithUnits = Field(
        ...,
        description="Soil moisture retention curve parameter (bexp)",
        alias="b",
        serialization_alias="b",
    )
    soil_params_satpsi: FloatWithUnits = Field(
        ...,
        description="Saturated soil suction (psisat)",
        alias="satpsi",
        serialization_alias="satpsi",
    )
    soil_params_quartz: FloatWithUnits = Field(
        default=FloatWithUnits(value=1.0, units="m"),
        description="Quartz content",
        alias="quartz",
        serialization_alias="quartz",
    )
    ice_fraction_scheme: IceFractionScheme = Field(..., description="Ice fraction scheme")
    soil_z: FloatListWithUnits = Field(
        default=FloatListWithUnits(value=[0.1, 0.3, 1.0, 2.0], units="m"),
        description="Soil depth layers in meters",
    )
    soil_temperature: FloatListWithUnits = Field(
        ...,
        description="Soil temperature in Kelvin for each layer",
        serialization_alias="soil_temperature_profile",
    )

    '''
    @field_validator("soil_temperature")
    @classmethod
    def validate_soil_temperature_length(cls, v, info):
        """Ensure soil_temperature has same length as soil_z"""
        # Get soil_z from the data being validated
        soil_z = info.data.get("soil_z", [0.1, 0.3, 1.0, 2.0])
        if len(v) != len(soil_z):
            raise ValueError(f"soil_temperature must have {len(soil_z)} values to match soil_z layers")
        return v
    '''

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        temp_values = ",".join([str(temp) for temp in self.soil_temperature])
        z_values = ",".join([str(z) for z in self.soil_z])

        return [
            f"soil_moisture_bmi={self.soil_moisture_bmi}",
            f"soil_params.smcmax={self.soil_params_smcmax}",
            f"soil_params.b={self.soil_params_b}",
            f"soil_params.satpsi={self.soil_params_satpsi}",
            f"soil_params.quartz={self.soil_params_quartz}",
            f"ice_fraction_scheme={self.ice_fraction_scheme.value}",
            f"soil_z={z_values}[m]",
            f"soil_temperature={temp_values}[K]",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        sft_bmi_file = output_path / f"{self.catchment}_bmi_config_sft.txt"
        with open(sft_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return sft_bmi_file


class AlbedoValues(enum.Enum):
    """A class to store land cover-derived albedo.

    Update land cover classes and corresponding values here.
    Values are [0, 100]
    """

    snow = 0.75
    ice = 0.3
    other = 0.2


class Albedo(BaseModel):
    """A model to handle `/topoflow/albedo` inputs and outputs.

    Note:
    This Literal will fail static type checking due to dynamically created values.
    However, generating dynamically keeps this function DRY and creates the appropriate API inputs.
    If changes to albedo values are needed, they are only made in `AlbedoValues`. `Albedo` will never change.
    """

    landcover: Literal[tuple(AlbedoValues._member_names_)]

    def get_landcover_albedo(v: str):
        """Return the albedo value"""
        return getattr(AlbedoValues, v)


class CalibratableScheme(enum.Enum):
    """The calibratable values to be used in Snow17"""

    MFMAX = 1.00
    MFMIN = 0.2
    UADJ = 0.05


class Snow17(BaseModel):
    """Pydantic model for Snow-17 module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    hru_id: str | int = Field(..., description="Unique divide identifier")
    hru_area: float = Field(..., description="Incremental areas of divide")
    latitude: float = Field(..., description="Y coordinates of divide centroid")
    elev: float = Field(..., description="Elevation from DEM")
    scf: float = Field(default=1.100, description="Snow Correction Factor")
    mfmax: float = Field(default=1.00, description="Maximum non-rain melt factor")
    mfmin: float = Field(default=0.20, description="Minimum non-rain melt factor")
    uadj: float = Field(default=0.05, description="Average wind function for rain on snow")
    si: float = Field(default=500.00, description="100% snow cover threshold")
    pxtemp: float = Field(default=1.000, description="Precipitation vs Snow threshold temperature")
    nmf: float = Field(default=0.150, description="maximum negative melt factor")
    tipm: float = Field(default=0.100, description="Antecedent snow temperature index")
    mbase: float = Field(default=0.000, description="Base Temperature for non-rain melt factor")
    plwhc: float = Field(default=0.030, description="Percent liquid water holding capacity")
    daygm: float = Field(default=0.000, description="Daily ground melt")
    adc1: float = Field(default=0.050, description="areal depletion curve, WE/Ai=0")
    adc2: float = Field(default=0.100, description="areal depletion curve, WE/Ai=0.1")
    adc3: float = Field(default=0.200, description="areal depletion curve, WE/Ai=0.2")
    adc4: float = Field(default=0.300, description="areal depletion curve, WE/Ai=0.3")
    adc5: float = Field(default=0.400, description="areal depletion curve, WE/Ai=0.4")
    adc6: float = Field(default=0.500, description="areal depletion curve, WE/Ai=0.5")
    adc7: float = Field(default=0.600, description="areal depletion curve, WE/Ai=0.6")
    adc8: float = Field(default=0.700, description="areal depletion curve, WE/Ai=0.7")
    adc9: float = Field(default=0.800, description="areal depletion curve, WE/Ai=0.8")
    adc10: float = Field(default=0.900, description="areal depletion curve, WE/Ai=0.9")
    adc11: float = Field(default=1.000, description="areal depletion curve, WE/Ai=1.0")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"hru_id: {self.hru_id}",
            f"hru_area: {self.hru_area}",
            f"latitude: {self.latitude}",
            f"elev: {self.elev}",
            f"scf: {self.scf}",
            f"mfmax: {self.mfmax}",
            f"mfmin: {self.mfmin}",
            f"uadj: {self.uadj}",
            f"si: {self.si}",
            f"pxtemp: {self.pxtemp}",
            f"nmf: {self.nmf}",
            f"tipm: {self.tipm}",
            f"mbase: {self.mbase}",
            f"plwhc: {self.plwhc}",
            f"daygm: {self.daygm}",
            f"adc1: {self.adc1}",
            f"adc2: {self.adc2}",
            f"adc3: {self.adc3}",
            f"adc4: {self.adc4}",
            f"adc5: {self.adc5}",
            f"adc6: {self.adc6}",
            f"adc7: {self.adc7}",
            f"adc8: {self.adc8}",
            f"adc9: {self.adc9}",
            f"adc10: {self.adc10}",
            f"adc11: {self.adc11}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        snow17_bmi_file = output_path / f"{self.catchment}_bmi_config_snow17.txt"
        with open(snow17_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return snow17_bmi_file


class SoilScheme(enum.Enum):
    """The calibratable scheme to be used in SMP"""

    CFE_SOIL_STORAGE = "conceptual"
    CFE_STORAGE_DEPTH = 2.0
    TOPMODEL_SOIL_STORAGE = "TopModel"
    TOPMODEL_WATER_TABLE_METHOD = "flux-based"
    LASAM_SOIL_STORAGE = "layered"
    LASAM_SOIL_MOISTURE = "constant"
    LASAM_SOIL_DEPTH_LAYERS = 2.0
    LASAM_WATER_TABLE_DEPTH = 10.0


class SMP(BaseModel):
    """Pydantic model for SMP module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    soil_params_smcmax: FloatWithUnits = Field(
        ...,
        description="Maximum soil moisture content",
        alias="smcmax",
        serialization_alias="smcmax",
    )
    soil_params_b: FloatWithUnits = Field(
        ...,
        description="Soil moisture retention curve parameter (bexp)",
        alias="b",
        serialization_alias="b",
    )
    soil_params_satpsi: FloatWithUnits = Field(
        ...,
        description="Saturated soil suction (psisat)",
        alias="satpsi",
        serialization_alias="satpsi",
    )
    soil_z: FloatListWithUnits = Field(
        default=FloatListWithUnits(value=[0.1, 0.3, 1.0, 2.0], units="m"),
        description="Soil depth layers in meters",
    )
    soil_moisture_fraction_depth: FloatWithUnits = Field(
        default=FloatWithUnits(value=0.4, units="m"), description="Soil moisture fraction depth in meters"
    )
    soil_storage_model: str | None = Field(
        ...,
        description="If conceptual, conceptual models are used for computing the soil moisture profile (e.g., CFE). If layered, layered-based soil moisture models are used (e.g., LGAR). If topmodel, topmodel's variables are used",
    )

    soil_storage_depth: FloatWithUnits | None = Field(
        ...,
        description="Depth of the soil reservoir model (e.g., CFE). Note: this depth can be different from the depth of the soil moisture profile which is based on soil_z",
    )

    water_table_based_method: str | None = Field(
        ...,
        description="Needed if soil_storage_model = topmodel. flux-based uses an iterative scheme, and deficit-based uses catchment deficit to compute soil moisture profile",
    )

    soil_moisture_profile_option: str | None = Field(
        ...,
        description="Constant for layered-constant profile. linear for linearly interpolated values between two consecutive layers. Needed if soil_storage_model = layered",
    )
    soil_depth_layers: FloatWithUnits | None = Field(
        ..., description="Absolute depth of soil layers. Needed if soil_storage_model = layered"
    )
    water_table_depth: FloatWithUnits | None = Field(default="NA", description="N/A")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        z_values = ",".join([str(z) for z in self.soil_z])

        return [
            f"soil_params.smcmax={self.soil_params_smcmax}",
            f"soil_params.b={self.soil_params_b}",
            f"soil_params.satpsi={self.soil_params_satpsi}",
            f"soil_z={z_values}[m]",
            f"soil_moisture_fraction_depth={self.soil_moisture_fraction_depth}[m]",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        smp_bmi_file = output_path / f"{self.catchment}_bmi_config_smp.txt"
        with open(smp_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return smp_bmi_file


class SacSmaValues(enum.Enum):
    """The values to be used in SAC SMA"""

    UZTWM = 75.0
    UZFWM = 30.0
    LZTWM = 150.0
    LZFPM = 300.0
    LZFSM = 150.0
    ADIMP = 0.0
    UZK = 0.3
    LZPK = 0.01
    LZSK = 0.1
    ZPERC = 100.0
    REXP = 2.0
    PCTIM = 0.0
    PFREE = 0.1
    RIVA = 0.0
    SIDE = 0.0
    RSERV = 0.3


class SacSma(BaseModel):
    """Pydantic model for SAC SMA module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    hru_id: str | int = Field(..., description="Unique divide identifier")
    hru_area: float = Field(..., description="Incremental areas of divide")
    uztwm: float | None = Field(
        default=float(SacSmaValues.UZTWM.value), description="Maximum upper zone tension water"
    )
    uzfwm: float | None = Field(
        default=float(SacSmaValues.UZFWM.value), description="Maximum upper zone free water"
    )
    lztwm: float | None = Field(
        default=float(SacSmaValues.LZTWM.value), description="Maximum lower zone tension water"
    )
    lzfpm: float | None = Field(
        default=float(SacSmaValues.LZFPM.value), description="Maximum lower zone free water, primary"
    )
    lzfsm: float | None = Field(
        default=float(SacSmaValues.LZFSM.value), description="Maximum lower zone free water, secondary"
    )
    adimp: float = Field(
        default=float(SacSmaValues.ADIMP.value), description="Additional 'impervious' area due to saturation"
    )
    uzk: float | None = Field(
        default=float(SacSmaValues.UZK.value), description="Upper zone recession coefficient"
    )
    lzpk: float | None = Field(
        default=float(SacSmaValues.LZPK.value), description="Lower zone recession coefficient, primary"
    )
    lzsk: float | None = Field(
        default=float(SacSmaValues.LZSK.value), description="Lower zone recession coefficient, secondary"
    )
    zperc: float | None = Field(
        default=float(SacSmaValues.ZPERC.value), description="Minimum percolation rate coefficient"
    )
    rexp: float | None = Field(
        default=float(SacSmaValues.REXP.value), description="Percolation equation exponent"
    )
    pctim: float = Field(
        default=float(SacSmaValues.PCTIM.value), description="Minimum percent impervious area"
    )
    pfree: float | None = Field(
        default=float(SacSmaValues.PFREE.value),
        description="Percent percolating directly to lower zone free water",
    )
    riva: float = Field(
        default=float(SacSmaValues.RIVA.value), description="Percent of the basin that is riparian area"
    )
    side: float = Field(
        default=float(SacSmaValues.SIDE.value),
        description="Portion of the baseflow which does not go to the stream",
    )
    rserv: float = Field(
        default=float(SacSmaValues.RSERV.value),
        description="Percent of lower zone free water not transferable to the lower zone tension water",
    )

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"hru_id: {self.hru_id}",
            f"hru_area: {self.hru_area}",
            f"uztwm: {self.uztwm}",
            f"uzfwm: {self.uzfwm}",
            f"lztwm: {self.lztwm}",
            f"lzfpm: {self.lzfpm}",
            f"lzfsm: {self.lzfsm}",
            f"adimp: {self.adimp}",
            f"uzk: {self.uzk}",
            f"lzpk: {self.lzpk}",
            f"lzsk: {self.lzsk}",
            f"zperc: {self.zperc}",
            f"rexp: {self.rexp}",
            f"pctim: {self.pctim}",
            f"pfree: {self.pfree}",
            f"riva: {self.riva}",
            f"side: {self.side}",
            f"rserv: {self.rserv}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        sacsma_bmi_file = output_path / f"{self.catchment}_bmi_config_sacsma.txt"
        with open(sacsma_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return sacsma_bmi_file


class LSTM(BaseModel):
    """
    Pydantic model for LSTM module configuration

    *Note: Per HF API, the following attributes for LSTM does not carry any relvant information:
    'train_cfg_file' & basin_name' -- remove if desire

    """

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    area_sqkm: float = Field(..., description="Allows bmi to adjust a weighted output")
    basin_id: str = Field(
        ..., description="Refer to https://github.com/NOAA-OWP/lstm/blob/master/bmi_config_files/README.md"
    )
    elev_mean: float = Field(..., description="Catchment mean elevation (m) above sea level")
    initial_state: str = Field(
        default="zero", description="This is an option to set the initial states of the model to zero."
    )
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    slope_mean: float = Field(..., description="Catchment mean slope (m km−1)")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"area_sqkm: {self.area_sqkm}",
            f"basin_id: {self.basin_id}",
            f"elev_mean: {self.elev_mean}",
            f"initial_state: {self.initial_state}",
            f"lat: {self.lat}",
            f"lon: {self.lon}",
            f"slope_mean: {self.slope_mean}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        lstm_bmi_file = output_path / f"{self.catchment}_bmi_config_lstm.txt"
        with open(lstm_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return lstm_bmi_file


class LASAM(BaseModel):
    """Pydantic model for LASAM module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    layer_thickness: str = Field(default="200.0[cm]", description="Thickness of each layer (array)")
    initial_psi: str = Field(default="2000.0[cm]", description="NA")
    forcing_resolution: str = Field(default="3600[sec]", description="NA")
    ponded_depth_max: str = Field(
        default="1.1[cm]",
        description="Maximum amount of ponded water that is allowed to accumulate on the soil surface",
    )
    use_closed_form_G: bool = Field(default=False, description="NA")
    layer_soil_type: float = Field(default="", description="Type of each soil layer (array)")
    max_soil_types: int = Field(default=15, description="NA")
    wilting_point_psi: str = Field(
        default="15495.0[cm]", description="Wilting point (the amount of water not available for plants)"
    )
    field_capacity_psi: str = Field(
        default="340.9[cm]",
        description="Capillary head corresponding to volumetric water content at which gravity drainage becomes slower",
        serialization_alias="field_capacity",
    )
    giuh_ordinates: list[float] = Field(default=[0.06, 0.51, 0.28, 0.12, 0.03], description="giuh")
    calib_params: bool = Field(default=True, description="NA")
    adaptive_timestep: bool = Field(default=True, description="NA")
    sft_coupled: bool = Field(..., description="NA")
    soil_z: list[float] = Field(default=[10, 30, 100.0, 200.0], description="NA")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        z_values = ",".join([str(z) for z in self.soil_z])
        giuh_ordinates = ",".join([str(giuh) for giuh in self.giuh_ordinates])

        return [
            f"layer_thickness={self.layer_thickness}",
            f"initial_psi={self.initial_psi}",
            f"forcing_resolution={self.forcing_resolution}",
            f"ponded_depth_max={self.ponded_depth_max}",
            f"use_closed_form_G={self.use_closed_form_G}",
            f"layer_soil_type={self.layer_soil_type}",
            f"max_soil_types={self.max_soil_types}",
            f"wilting_point_psi={self.wilting_point_psi}",
            f"field_capacity_psi={self.field_capacity_psi}",
            f"giuh_ordinates={giuh_ordinates}",
            f"calib_params={self.calib_params}",
            f"adaptive_timestep={self.adaptive_timestep}",
            f"sft_coupled={self.sft_coupled}",
            f"soil_z={z_values}[cm]",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        lasam_bmi_file = output_path / f"{self.catchment}_bmi_config_lasam.txt"
        with open(lasam_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return lasam_bmi_file


class NoahOwpModular(BaseModel):
    """Pydantic model for Noah OWP module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    general_table: str = Field(default="GENPARM.TBL", description="General param tables and misc params")
    soil_table: str = Field(default="SOILPARM.TBL", description="Soil param table")
    noahowp_table: str = Field(default="MPTABLE.TBL", description="Model param tables (includes veg)")
    soil_class_name: str = Field(default="STAS", description="Soil class data source - 'STAS' or 'STAS-RUC'")
    veg_class_name: str = Field(
        default="USGS", description="Vegetation class data source - 'MODIFIED_IGBP_MODIS_NOAH' or 'USGS'"
    )
    lat: float = Field(..., description="Latitude [degrees]  (-90 to 90)")
    lon: float = Field(..., description="Longitude [degrees] (-180 to 180)")
    terrain_slope: float = Field(..., description="Terrain slope [degrees]")
    azimuth: float = Field(..., description="Terrain azimuth or aspect [degrees clockwise from north]")
    ZREF: float = Field(default=10.0, description="Measurement height for wind speed (m)")
    rain_snow_thresh: float = Field(
        default=0.5, description="Rain-snow temperature threshold (degrees Celsius)"
    )
    precip_phase_option: int = Field(default=6, description="NA")
    snow_albedo_option: int = Field(default=1, description="NA")
    dynamic_veg_option: int = Field(default=4, description="NA")
    runoff_option: int = Field(default=3, description="NA")
    drainage_option: int = Field(default=8, description="NA")
    frozen_soil_option: int = Field(default=1, description="NA")
    dynamic_vic_option: int = Field(default=1, description="NA")
    radiative_transfer_option: int = Field(default=3, description="NA")
    sfc_drag_coeff_option: int = Field(default=1, description="NA")
    canopy_stom_resist_option: int = Field(default=1, description="NA")
    crop_model_option: int = Field(default=0, description="NA")
    snowsoil_temp_time_option: int = Field(default=3, description="NA")
    soil_temp_boundary_option: int = Field(default=2, description="NA")
    supercooled_water_option: int = Field(default=1, description="NA")
    stomatal_resistance_option: int = Field(default=1, description="NA")
    evap_srfc_resistance_option: int = Field(default=4, description="NA")
    subsurface_option: int = Field(default=2, description="NA")
    isltyp: float = Field(..., description="Soil texture class")
    nsoil: int = Field(default=4, description="Number of soil levels")
    nsnow: int = Field(default=3, description="Number of snow levels")
    nveg: int = Field(default=27, description="Number of vegetation type")
    vegtyp: int = Field(..., description="Vegetation type")
    croptype: int = Field(
        default=0, description="Crop type (0 = no crops; this option is currently inactive)"
    )
    sfctyp: int = Field(..., description="Land surface type, 1:soil, 2:lake")
    soilcolor: int = Field(default=4, description="Soil color code")
    dzsnso: list[float] = Field(
        default=[0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 1.0], description="Level thickness [m]"
    )
    sice: list[float] = Field(default=[0.0, 0.0, 0.0, 0.0], description="Initial soil ice profile [m3/m3]")
    sh2o: list[float] = Field(default=[0.3, 0.3, 0.3, 0.3], description="Initial soil liquid profile [m3/m3]")
    zwt: int = Field(default=-2.0, description="Initial water table depth below surface [m] ")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        dzsnso = ",".join([str(th_lvl) for th_lvl in self.dzsnso])
        sice = ",".join([str(ice) for ice in self.sice])
        sh2o = ",".join([str(h2o) for h2o in self.sh2o])

        return [
            f"general_table={self.general_table}",
            f"soil_table={self.soil_table}",
            f"noahowp_table={self.noahowp_table}",
            f"soil_class_name={self.soil_class_name}",
            f"veg_class_name={self.veg_class_name}",
            f"lat={self.lat} [degrees]",
            f"lon={self.lon} [degrees]",
            f"terrain_slope={self.terrain_slope} [degrees]",
            f"azimuth={self.azimuth}  [degrees clockwise from north]",
            f"ZREF={self.ZREF} [m]",
            f"rain_snow_thresh={self.rain_snow_thresh} [C]",
            f"precip_phase_option={self.precip_phase_option}",
            f"snow_albedo_option={self.snow_albedo_option}",
            f"dynamic_veg_option={self.dynamic_veg_option}",
            f"runoff_option={self.runoff_option}",
            f"drainage_option={self.drainage_option}",
            f"frozen_soil_option={self.frozen_soil_option}",
            f"dynamic_vic_option={self.dynamic_vic_option}",
            f"radiative_transfer_option={self.radiative_transfer_option}",
            f"sfc_drag_coeff_option={self.sfc_drag_coeff_option}",
            f"canopy_stom_resist_option={self.canopy_stom_resist_option}",
            f"crop_model_option={self.crop_model_option}",
            f"snowsoil_temp_time_option={self.snowsoil_temp_time_option}",
            f"soil_temp_boundary_option={self.soil_temp_boundary_option}",
            f"supercooled_water_option={self.supercooled_water_option}",
            f"stomatal_resistance_option={self.stomatal_resistance_option}",
            f"evap_srfc_resistance_option={self.evap_srfc_resistance_option}",
            f"subsurface_option={self.subsurface_option}",
            f"isltyp={self.isltyp}",
            f"nsoil={self.nsoil}",
            f"nsnow={self.nsnow}",
            f"nveg={self.nveg}",
            f"vegtyp={self.vegtyp}",
            f"croptype={self.croptype}",
            f"sfctyp={self.sfctyp}",
            f"soilcolor={self.soilcolor}",
            f"dzsnso={dzsnso} [m]",
            f"sice={sice} [m3/m3]",
            f"sh2o={sh2o} [m3/m3]",
            f"zwt={self.zwt} [m]",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        noahowp_bmi_file = output_path / f"{self.catchment}_bmi_config_noahowp.txt"
        with open(noahowp_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return noahowp_bmi_file


# TODO: integrate TRoute-config class for creating/validating
class TRoute(BaseModel):
    """Pydantic model for T-Route module configuration"""

    reservoir_da: ClassVar[dict] = {
        "reservoir_persistence_da": {
            "reservoir_persistence_usgs": False,
            "reservoir_persistence_usace": False,
        },
        "reservoir_rfc_da": {
            "reservoir_rfc_forecasts": False,
            "reservoir_rfc_forecasts_time_series_path": None,
            "reservoir_rfc_forecasts_lookback_hours": 28,
            "reservoir_rfc_forecasts_offset_hours": 28,
            "reservoir_rfc_forecast_persist_days": 11,
        },
        "reservoir_parameter_file": None,
    }

    stream_da: ClassVar[dict] = {
        "streamflow_nudging": False,
        "diffusive_streamflow_nudging": False,
        "gage_segID_crosswalk_file": None,
    }

    dupseg: ClassVar[list] = [
        "717696",
        "1311881",
        "3133581",
        "1010832",
        "1023120",
        "1813525",
        "1531545",
        "1304859",
        "1320604",
        "1233435",
        "11816",
        "1312051",
        "2723765",
        "2613174",
        "846266",
        "1304891",
        "1233595",
        "1996602",
        "2822462",
        "2384576",
        "1021504",
        "2360642",
        "1326659",
        "1826754",
        "572364",
        "1336910",
        "1332558",
        "1023054",
        "3133527",
        "3053788",
        "3101661",
        "2043487",
        "3056866",
        "1296744",
        "1233515",
        "2045165",
        "1230577",
        "1010164",
        "1031669",
        "1291638",
        "1637751",
    ]

    ntwk_columns: ClassVar[dict] = {
        "key": "id",
        "downstream": "toid",
        "dx": "lengthkm",
        "n": "n",
        "ncc": "nCC",
        "s0": "So",
        "bw": "BtmWdth",
        "waterbody": "WaterbodyID",
        "gages": "gage",
        "tw": "TopWdth",
        "twcc": "TopWdthCC",
        "musk": "MusK",
        "musx": "MusX",
        "cs": "ChSlp",
        "alt": "alt",
    }

    # Default values
    bmi_parameters = {
        "flowpath_columns": ["id", "toid", "lengthkm"],
        "attributes_columns": [
            "attributes_id",
            "gage",
            "WaterbodyID",
            "MusK",
            "MusX",
            "n",
            "So",
            "ChSlp",
            "BtmWdth",
            "nCC",
            "TopWdthCC",
            "TopWdth",
        ],
        "waterbody_columns": [
            "hl_link",
            "ifd",
            "LkArea",
            "LkMxE",
            "OrificeA",
            "OrificeC",
            "OrificeE",
            "WeirC",
            "WeirE",
            "WeirL",
        ],
        "network_columns": ["network_id", "hydroseq", "hl_uri"],
    }

    log_param = {"showtiming": True, "log_level": "DEBUG"}

    network_topology_parameters = {
        "supernetwork_parameters": {
            "network_type": "HYFeaturesNetwork",
            "geo_file_path": "",
            "columns": ntwk_columns,
            "duplicate_wb_segments": dupseg,
        },
        "waterbody_parameters": {
            "break_network_at_waterbodies": True,
            "level_pool": {"level_pool_waterbody_parameter_file_path": ""},
        },
    }

    compute_parameters = {
        "parallel_compute_method": "by-subnetwork-jit-clustered",
        "subnetwork_target_size": 10000,
        "cpu_pool": 16,
        "compute_kernel": "V02-structured",
        "assume_short_ts": True,
        "restart_parameters": {"start_datetime": ""},
        "forcing_parameters": {
            "qts_subdivisions": 12,
            "dt": 300,
            "qlat_input_folder": ".",
            "qlat_file_pattern_filter": "nex-*",
            "nts": 5,
            "max_loop_size": divmod(5 * 300, 3600)[0] + 1,
        },
        "data_assimilation_parameters": {
            "usgs_timeslices_folder": None,
            "usace_timeslices_folder": None,
            "timeslice_lookback_hours": 48,
            "qc_threshold": 1,
            "streamflow_da": stream_da,
            "reservoir_da": reservoir_da,
        },
    }

    output_parameters = {
        "stream_output": {
            "stream_output_directory": ".",
            "stream_output_time": divmod(5 * 300, 3600)[0] + 1,
            "stream_output_type": ".nc",
            "stream_output_internal_frequency": 60,
        }
    }

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    bmi_parameters: dict = Field(default=bmi_parameters, description="BMI Parameters")
    log_param: dict = Field(default=log_param, description="Log Parameters")
    network_topology_parameters: dict = Field(
        default=network_topology_parameters, description="Network Topology Parameters"
    )
    compute_parameters: dict = Field(default=compute_parameters, description="Compute Parameters")
    output_parameters: dict = Field(default=output_parameters, description="Output Parameters")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return {
            f"bmi_parameters: {self.bmi_parameters}",
            f"log_parameters: {self.log_param}",
            f"network_topology_parameters: {self.network_topology_parameters}",
            f"compute_parameters: {self.comp_param}",
            f"output_parameters: {self.output_parameters}",
        }

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        troute_bmi_file = output_path / f"{self.catchment}_bmi_config_troute.txt"
        with open(troute_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return troute_bmi_file


class Topmodel(BaseModel):
    """Pydantic model for Topmodel module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    divide_id: str | int = Field(..., description="The catchment ID")
    num_sub_catchments: int = Field(default=1, description="Number of sub catchments")
    imap: int = Field(default=1, description="NA")
    twi: list[dict] = Field(default=[{"twi": "dist_4.twi"}], description="NA")
    num_topodex_values: int = Field(..., description="NA")
    area: int = Field(default=1, description="NA")
    num_channels: int = Field(default=1, description="Number of channels")
    cum_dist_area_with_dist: float = Field(default=1.0, description="NA")
    dist_from_outlet: float = Field(..., description="NA")
    szm: float = Field(default=0.0125, description="Exponential decline parameter of transmissivity")
    t0: float = Field(
        default=0.000075, description="Downslope transmissivity when the soil is saturated to the surface"
    )
    td: float = Field(default=20, description="Unsaturated zone time delay per unit storage deficit")
    chv: float = Field(default=1000, description="Average channel flow velocity")
    rv: float = Field(default=1000, description="Internal overland flow routing velocity")
    srmax: float = Field(default=0.04, description="Maximum root zone storage deficit")
    Q0: float = Field(default=0.0000328, description="Initial subsurface flow per unit area")
    sr0: float = Field(default=0, description="Initial root zone storage deficit below field capacity (m)")
    infex: float = Field(
        default=0,
        description="Whether to call subroutine to do infiltration excess calcs, Not typically appropriate in catchments where TOPMODEL is applicable (i.e., shallow highly permeable  soils). 0 = FALSE (default)",
    )
    xk0: float = Field(default=2, description="Surface soil hydraulic conductivity")
    hf: float = Field(default=0.1, description="Wetting front suction for Green & Ampt solution.")
    dth: float = Field(default=0.1, description="Water content change across the wetting front")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"catchment={self.catchment}",
            f"divide_id={self.divide_id}",
            f"num_sub_catchments={self.num_sub_catchments}",
            f"imap={self.imap}",
            f"twi={self.twi}",
            f"num_topodex_values={self.num_topodex_values}area={self.area}",
            f"num_channels={self.num_channels}",
            f"cum_dist_area_with_dist={self.cum_dist_area_with_dist}",
            f"dist_from_outlet={self.dist_from_outlet}",
            f"szm={self.szm}",
            f"t0={self.t0}",
            f"td={self.td}",
            f"chv={self.chv}",
            f"rv={self.rv}",
            f"srmax={self.srmax}",
            f"Q0={self.Q0}",
            f"sr0={self.sr0}",
            f"infex={self.infex}",
            f"xk0={self.xk0}",
            f"hf={self.hf}",
            f"dth={self.dth}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        topmodel_bmi_file = output_path / f"{self.catchment}_bmi_config_topmodel.txt"
        with open(topmodel_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return topmodel_bmi_file


class TopoFlowValues(enum.Enum):
    """Default parameter values for Topoflow"""

    H_ACTIVE_LAYER = 0.125
    H0_SNOW = 5.0
    H0_ICE = 2.0
    H0_SWE = 0.25
    H0_IWE = 1.834
    T_RAIN_SNOW = 0.0


class Topoflow(BaseModel):
    """Pydantic model for Topoflow module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    site_prefix: str | int = Field(..., description="The catchment ID")
    da: float = Field(..., description="drainage area")
    slope: float = Field(..., description="terrain slope in degrees")
    aspect: float = Field(..., description="terrain aspect in degrees")
    lat: float = Field(..., description="Y coordinates of divide centroid")
    lon: float = Field(..., description="X coordinates of divide centroid")
    elev: float = Field(..., description="Elevation from DEM")
    h_active_layer: float = Field(
        default=TopoFlowValues.H_ACTIVE_LAYER.value,
        description="",
    )
    h0_snow: float = Field(
        default=TopoFlowValues.H0_SNOW.value,
        description="",
    )
    h0_ice: float = Field(
        default=TopoFlowValues.H0_ICE.value,
        description="",
    )
    h0_swe: float = Field(
        default=TopoFlowValues.H0_SWE.value,
        description="",
    )
    h0_iwe: float = Field(
        default=TopoFlowValues.H0_IWE.value,
        description="",
    )
    T_rain_snow: float = Field(
        default=TopoFlowValues.T_RAIN_SNOW.value,
        description="",
    )
    glacier_percent: float = Field(..., description="Percentage of catchment that is glaciated")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"site_prefix={self.site_prefix}",
            f"da={self.da}",
            f"slope={self.slope}",
            f"aspect={self.aspect}",
            f"lon={self.lon}",
            f"lat={self.lat}",
            f"elev={self.elev}",
            f"h_active_layer={self.h_active_layer}",
            f"h0_snow={self.h0_snow}",
            f"h0_ice={self.h0_ice}",
            f"h0_swe={self.h0_swe}",
            f"h0_iwe={self.h0_iwe}",
            f"T_rain_snow={self.T_rain_snow}",
            f"glaciated_percent={self.glacier_percent}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        topoflow_bmi_file = output_path / f"{self.site_prefix}_bmi_config_topoflow.txt"
        with open(topoflow_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return topoflow_bmi_file


class UEBValues(enum.Enum):
    """The calibratable values to be used in UEB"""

    JAN_TEMP = 11.04395
    FEB_TEMP = 11.79382
    MAR_TEMP = 12.72711
    APR_TEMP = 13.67701
    MAY_TEMP = 13.70334
    JUN_TEMP = 13.76782
    JUL_TEMP = 13.90212
    AUG_TEMP = 13.9958
    SEP_TEMP = 14.04895
    OCT_TEMP = 13.44001
    NOV_TEMP = 11.90162
    DEC_TEMP = 10.71597
    USIC = 0.0
    WSIS = 0.0
    TIC = 0.0
    WCIC = 0.0
    DF = 1.0
    AEP = 0.1
    CC = 0.4
    HCAN = 5.0
    LAI = 2
    SBAR = 6.6
    YCAGE = 2.5
    SUBALB = 0.25
    SUBTYPE = 0
    GSURF = 0.0
    TS_LAST = -9999


class UEB(BaseModel):
    """Pydantic model for UEB module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    aspect: float = Field(..., description="Aspect computed from DEM")
    slope: float = Field(..., description="Slope")
    longitude: float = Field(..., description="X coordinates of divide centroid")
    latitude: float = Field(..., description="Y coordinates of divide centroid")
    elevation: float = Field(..., description="Elevation from DEM")
    standard_atm_pressure: float = Field(..., description="Standard atmospheric pressuure (atm)")
    jan_temp_range: float | None = Field(default=UEBValues.JAN_TEMP.value, description="Average temperature")
    feb_temp_range: float | None = Field(default=UEBValues.FEB_TEMP.value, description="Average temperature")
    mar_temp_range: float | None = Field(default=UEBValues.MAR_TEMP.value, description="Average temperature")
    apr_temp_range: float | None = Field(default=UEBValues.APR_TEMP.value, description="Average temperature")
    may_temp_range: float | None = Field(default=UEBValues.MAY_TEMP.value, description="Average temperature")
    jun_temp_range: float | None = Field(default=UEBValues.JUN_TEMP.value, description="Average temperature")
    jul_temp_range: float | None = Field(default=UEBValues.JUL_TEMP.value, description="Average temperature")
    aug_temp_range: float | None = Field(default=UEBValues.AUG_TEMP.value, description="Average temperature")
    sep_temp_range: float | None = Field(default=UEBValues.SEP_TEMP.value, description="Average temperature")
    oct_temp_range: float | None = Field(default=UEBValues.OCT_TEMP.value, description="Average temperature")
    nov_temp_range: float | None = Field(default=UEBValues.NOV_TEMP.value, description="Average temperature")
    dec_temp_range: float | None = Field(default=UEBValues.DEC_TEMP.value, description="Average temperature")
    Usic: float = Field(default=UEBValues.USIC.value, description="Energy content initial condition (kg m-3)")
    Wsis: float = Field(
        default=UEBValues.WSIS.value, description="Snow water equivalent initial condition (m)"
    )
    Tic: float = Field(
        default=UEBValues.TIC.value, description="Snow surface dimensionless age initial condition"
    )
    Wcic: float = Field(
        default=UEBValues.WCIC.value, description="Snow water equivalent of canopy condition(m)"
    )
    df: float = Field(default=UEBValues.DF.value, description="Drift factor multiplier")
    Aep: float = Field(default=UEBValues.AEP.value, description="Albedo extinction coefficient")
    cc: float = Field(default=UEBValues.CC.value, description="Canopy coverage fraction")
    hcan: float = Field(default=UEBValues.HCAN.value, description="Canopy height")
    lai: float = Field(default=UEBValues.LAI.value, description="Leaf area index")
    Sbar: float = Field(
        default=UEBValues.SBAR.value, description="Maximum snow load held per unit branch area"
    )
    ycage: float = Field(
        default=UEBValues.YCAGE.value, description="Forest age flag for wind speed profile parameterization"
    )
    subalb: float = Field(
        default=UEBValues.SUBALB.value,
        description="Albedo (fraction 0-1) of the substrate beneath the snow (ground, or glacier)",
    )
    subtype: float = Field(
        default=UEBValues.SUBTYPE.value,
        description="Type of beneath snow substrate encoded as (0 = Ground/Non Glacier, 1=Clean"
        " Ice/glacier, 2= Debris covered ice/glacier, 3= Glacier snow accumulation zone",
    )
    gsurf: float = Field(
        default=UEBValues.GSURF.value,
        description="The fraction of surface melt that runs off (e.g. from a glacier",
    )
    ts_last: float = Field(default=UEBValues.TS_LAST.value, description="Average temperature")

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        return [
            f"aspect: {self.aspect}",
            f"slope: {self.slope}",
            f"longitude: {self.longitude}",
            f"latitude: {self.latitude}",
            f"elevation: {self.elevation}",
            f"standard_atm_pressure: {self.standard_atm_pressure}",
            f"jan_temp_range: {self.jan_temp_range}",
            f"feb_temp_range: {self.feb_temp_range}",
            f"mar_temp_range: {self.mar_temp_range}",
            f"apr_temp_range: {self.apr_temp_range}",
            f"may_temp_range: {self.may_temp_range}",
            f"jun_temp_range: {self.jun_temp_range}",
            f"jul_temp_range: {self.jul_temp_range}",
            f"aug_temp_range: {self.aug_temp_range}",
            f"sep_temp_range: {self.sep_temp_range}",
            f"oct_temp_range: {self.oct_temp_range}",
            f"nov_temp_range: {self.nov_temp_range}",
            f"dec_temp_range: {self.dec_temp_range}",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        ueb_bmi_file = output_path / f"{self.catchment}_bmi_config_ueb.txt"
        with open(ueb_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return ueb_bmi_file


class CFEValues(enum.Enum):
    """The default values & schemes to be used in CFE"""

    SRFC_RUNOFF_SCHEME = "GIUH"
    ICE_CONTENT_THR = 0.15
    SCHAAKE = "Schaake"
    XINANJIANG = "Xinanjiang"
    A_XINANJIANG_INFLECT = -0.2
    B_XINANJIANG_SHAPE = 0.66
    X_XINANJIANG_SHAPE = 0.02
    SOIL_EXPON = 1.0
    SOIL_EXPON_SECONDARY = 1.0
    MAX_GW_STORAGE = 0.05
    GW_STORAGE = 0.05
    ALPHA_FC = 0.33
    SOIL_STORAGE = 0.5
    K_NASH = 0.003
    K_LF = 0.01
    NASH_STORAGE = [0.0, 0.0]
    GIUH = [0.55, 0.25, 0.2]
    URBAN_FRACT = 0.01
    SOIL_DEPTH = 2.0
    SOIL_WLTSMC = 0.439
    SOIL_SMCMAX = 0.439
    SOIL_SLOP = 0.05
    SOIL_SATPSI = 0.355
    SOIL_SATDK = 0.00000338
    SOIL_B = 4.05
    CGW = 0.000018
    EXPON = 3
    REFKDT = 1.0
    IS_AET = False
    SOIL_LAYER_DEPTHS = [0.1, 0.4, 1.0, 2.0]
    MAX_ROOTZONE_LAYER = 2.0


class CFEUnits(enum.Enum):
    """Units for CFE parameters"""

    ICE_CONTENT_THR = "m"
    A_XINANJIANG_INFLECT = None
    B_XINANJIANG_SHAPE = None
    X_XINANJIANG_SHAPE = None
    SOIL_EXPON = None
    SOIL_EXPON_SECONDARY = None
    MAX_GW_STORAGE = "m"
    GW_STORAGE = "m/m"
    ALPHA_FC = None
    SOIL_STORAGE = "m/m"
    K_NASH = "1/m"
    K_LF = None
    NASH_STORAGE = None
    GIUH = None
    URBAN_FRACT = None
    SOIL_DEPTH = "m"
    SOIL_WLTSMC = "m/m"
    SOIL_SMCMAX = "m/m"
    SOIL_SLOP = "m/m"
    SOIL_SATPSI = "m"
    SOIL_SATDK = "m/s"
    SOIL_B = None
    CGW = "m/hr"
    EXPON = None
    REFKDT = None
    SOIL_LAYER_DEPTHS = "m"
    MAX_ROOTZONE_LAYER = "m"


class CFE(BaseModel):
    """Pydantic model for CFE module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str | int = Field(..., description="The catchment ID")
    surface_water_partitioning_scheme: str = Field(..., description="Selects Xinanjiang or Schaake")
    surface_runoff_scheme: str = Field(
        default=CFEValues.SRFC_RUNOFF_SCHEME.value,
        description="Accepts  1 or GIUH for GIUH and  2 or NASH_CASCADE for Nash Cascade; default is GIUH, version 1 is GIUH, Version 2 is Nash",
    )
    is_sft_coupled: bool = Field(
        False,
        description="Optional. Turns on/off the CFE coupling with the SoilFreezeThaw. If this parameter is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then ice_content_threshold also needs to be defined in the config file.",
    )
    ice_content_threshold: FloatWithUnits | None = Field(
        default=FloatWithUnits(value=CFEValues.ICE_CONTENT_THR.value, units=CFEUnits.ICE_CONTENT_THR.value),
        description="Optional. This represents the ice content above which soil is impermeable. If this is_sft_couple is defined to be True (or 1) in the config file and surface_partitioning_scheme=Schaake, then this also needs to be defined in the config file.",
    )
    soil_params_b: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_B.value, units=CFEUnits.SOIL_B.value),
        description="Beta exponent on Clapp-Hornberger (1978) soil water relations",
        serialization_alias="b",
    )
    soil_params_satdk: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_SATDK.value, units=CFEUnits.SOIL_SATDK.value),
        description="Saturated hydraulic conductivity",
        serialization_alias="satdk",
    )
    soil_params_satpsi: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_SATPSI.value, units=CFEUnits.SOIL_SATPSI.value),
        description="Saturated capillary head",
        serialization_alias="satpsi",
    )
    soil_params_slop: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_SLOP.value, units=CFEUnits.SOIL_SLOP.value),
        description="This factor (0-1) modifies the gradient of the hydraulic head at the soil bottom.  0=no-flow.",
        serialization_alias="slope",
    )
    soil_params_smcmax: FloatWithUnits = Field(
        default=FloatWithUnits(
            value=CFEValues.SOIL_SMCMAX.value,
            units=CFEUnits.SOIL_SMCMAX.value,
        ),
        description="Saturated soil moisture content (Maximum soil moisture content)",
        serialization_alias="maxsmc",
    )
    soil_params_wltsmc: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_WLTSMC.value, units=CFEUnits.SOIL_WLTSMC.value),
        description="Wilting point soil moisture content (< soil_params.smcmax)",
        serialization_alias="wltsmc",
    )
    soil_params_expon: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_EXPON.value, units=CFEUnits.SOIL_EXPON.value),
        description="Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
        json_schema_extra={"units": "here are units"},
        serialization_alias="soil_params.expon",
    )
    soil_params_expon_secondary: FloatWithUnits = Field(
        default=FloatWithUnits(
            value=CFEValues.SOIL_EXPON_SECONDARY.value, units=CFEUnits.SOIL_EXPON_SECONDARY.value
        ),
        description="	Optional; defaults to 1, This parameter defines the soil reservoirs to be linear, Use linear reservoirs",
        serialization_alias="soil_params.expon_secondary",
    )
    max_gw_storage: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.MAX_GW_STORAGE.value, units=CFEUnits.MAX_GW_STORAGE.value),
        description="Maximum storage in the conceptual reservoir",
    )
    Cgw: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.CGW.value, units=CFEUnits.CGW.value),
        description="Primary outlet coefficient",
    )
    expon: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.EXPON.value, units=CFEUnits.EXPON.value),
        description="Exponent parameter for nonlinear ground water reservoir (1.0 for linear reservoir)",
    )
    gw_storage: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.GW_STORAGE.value, units=CFEUnits.GW_STORAGE.value),
        description="Initial condition for groundwater reservoir - it is the ground water as a decimal fraction of the maximum groundwater storage (max_gw_storage) for the initial timestep",
    )
    alpha_fc: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.ALPHA_FC.value, units=CFEUnits.ALPHA_FC.value),
        description="Alpha at fc for clapp hornberger (field capacity)",
    )
    soil_storage: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_STORAGE.value, units=CFEUnits.SOIL_STORAGE.value),
        description="Initial condition for soil reservoir - it is the water in the soil as a decimal fraction of maximum soil water storage (smcmax x depth) for the initial timestep. Default = 0.5",
    )
    K_nash: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.K_NASH.value, units=CFEUnits.K_NASH.value),
        description="Nash Config param for lateral subsurface runoff (Nash discharge to storage ratio)",
        json_schema_extra={"units": "units"},
        serialization_alias="Kn",
    )
    K_lf: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.K_LF.value, units=CFEUnits.K_LF.value),
        description="Nash Config param - primary reservoir",
        serialization_alias="Klf",
    )
    nash_storage: FloatListWithUnits = Field(
        default=FloatListWithUnits(value=CFEValues.NASH_STORAGE.value, units=CFEUnits.NASH_STORAGE.value),
        description="Nash Config param - secondary reservoir",
    )
    giuh_ordinates: FloatListWithUnits = Field(
        default=FloatListWithUnits(value=CFEValues.GIUH.value, units=CFEUnits.GIUH.value),
        description="Giuh (geomorphological instantaneous unit hydrograph) ordinates in dt time steps",
    )
    a_Xinanjiang_inflection_point_parameter: FloatWithUnits | None = Field(
        default=FloatWithUnits(
            value=CFEValues.A_XINANJIANG_INFLECT.value, units=CFEUnits.A_XINANJIANG_INFLECT.value
        ),
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    b_Xinanjiang_shape_parameter: FloatWithUnits | None = Field(
        default=FloatWithUnits(
            value=CFEValues.B_XINANJIANG_SHAPE.value, units=CFEUnits.B_XINANJIANG_SHAPE.value
        ),
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    x_Xinanjiang_shape_parameter: FloatWithUnits | None = Field(
        default=FloatWithUnits(
            value=CFEValues.X_XINANJIANG_SHAPE.value, units=CFEUnits.X_XINANJIANG_SHAPE.value
        ),
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    urban_decimal_fraction: FloatWithUnits | None = Field(
        default=FloatWithUnits(value=CFEValues.URBAN_FRACT.value, units=CFEUnits.URBAN_FRACT.value),
        description="When surface_water_partitioning_scheme=Xinanjiang",
    )
    refkdt: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.REFKDT.value, units=CFEUnits.REFKDT.value),
        description="Reference Soil Infiltration Parameter (used in runoff formulation)",
    )
    soil_params_depth: FloatWithUnits = Field(
        default=FloatWithUnits(value=CFEValues.SOIL_DEPTH.value, units=CFEUnits.SOIL_DEPTH.value),
        description="Soil depth",
        serialization_alias="soil_params.depth",
    )
    is_aet_rootzone: bool = Field(default=CFEValues.IS_AET.value, description="Turn on rootzone AET")
    soil_layer_depths: FloatListWithUnits | None = Field(
        default=FloatListWithUnits(
            value=CFEValues.SOIL_LAYER_DEPTHS.value, units=CFEUnits.SOIL_LAYER_DEPTHS.value
        ),
        description="array of depths from the surface for AET",
    )
    max_rootzone_layer: FloatWithUnits | None = Field(
        default=FloatWithUnits(
            value=CFEValues.MAX_ROOTZONE_LAYER.value, units=CFEUnits.MAX_ROOTZONE_LAYER.value
        ),
        description="layer of the soil that is the maximum root zone depth",
    )

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        nash_storage = ",".join([str(n) for n in self.nash_storage])
        giuh_ordinates = ",".join([str(giuh) for giuh in self.giuh_ordinates])
        return [
            f"surface_partitioning_scheme: {self.surface_partitioning_scheme}",
            f"surface_runoff_scheme: {self.surface_runoff_scheme}",
            f"is_sft_coupled: {self.is_sft_coupled}",
            f"ice_content_threshold: {self.ice_content_thresh}",
            f"soil_params.b: {self.soil_params_b}",
            f"soil_params.satdk: {self.soil_params_satdk}[m/s]",
            f"soil_params.satpsi: {self.soil_params_satpsi}[m]",
            f"soil_params.slop: {self.soil_params_slop}[m/m]",
            f"soil_params.smcmax: {self.soil_params_smcmax}[m/m]",
            f"soil_params.wltsmc: {self.soil_params_wltsmc}[m/m]",
            f"soil_params.expon: {self.soil_params_expon}",
            f"soil_params.expon_secondary: {self.soil_params_expon_secondary}",
            f"max_gw_storage: {self.max_gw_storage}[m]",
            f"Cgw: {self.Cgw}[m/hr]",
            f"expon: {self.expon}",
            f"gw_storage: {self.gw_storage}[m/m]",
            f"alpha_fc: {self.alpha_fc}",
            f"soil_storage: {self.soil_storage}[m/m]",
            f"K_nash: {self.K_nash}[1/m]",
            f"K_lf: {self.K_lf}",
            f"nash_storage: {nash_storage}",
            f"giuh_ordinates: {giuh_ordinates}",
            f"a_Xinanjiang_inflection_point_parameter: {self.a_Xinanjiang_inflection_point_parameter}",
            f"b_Xinanjiang_shape_parameter: {self.b_Xinanjiang_shape_parameter}",
            f"x_Xinanjiang_shape_parameter: {self.x_Xinanjiang_shape_parameter}",
            f"urban_decimal_fraction: {self.urban_decimal_fraction}",
            f"refkdt: {self.refkdt}",
            f"soil_params.depth: {self.soil_params_depth}[m]",
        ]

    def model_dump_config(self, output_path: Path) -> Path:
        """Outputs the BaseModel to a BMI Config file

        Parameters
        ----------
        output_path : Path
            The path for the config file to be written to

        Returns
        -------
        Path
            The path to the written config file
        """
        file_output = self.to_bmi_config()
        cfe_bmi_file = output_path / f"{self.catchment}_bmi_config_cfe.txt"
        with open(cfe_bmi_file, "w") as f:
            f.write("\n".join(file_output))
        return cfe_bmi_file
