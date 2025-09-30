"""A file to host schemas for all NWM modules. Based off the table from https://confluence.nextgenwaterprediction.com/pages/viewpage.action?spaceKey=NGWPC&title=BMI+Exchange+Items+and+Module+Parameters"""

import enum
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NWMProtocol(Protocol):
    """Protocol defining the interface that configuration NWM BaseModel classes should implement."""

    def to_bmi_config(self) -> list[str]:
        """Converts the contents of the base class to a BMI config for that specific module"""
        ...

    def model_dump_config(self, output_path: Path) -> Path:  # Changed to return Path
        """Outputs the BaseModel to a BMI Config file"""
        ...


class IceFractionScheme(str, enum.Enum):
    """The ice fraction scheme to be used in SFT"""

    SCHAAKE = "Schaake"
    XINANJIANG = "Xinanjiang"


class SFT(BaseModel):
    """Pydantic model for SFT (Snow Freeze Thaw) module configuration"""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
    catchment: str = Field(..., description="The catchment ID")
    verbosity: str = Field(default="none", description="Verbosity level")
    soil_moisture_bmi: int = Field(default=1, description="Soil moisture BMI parameter")
    end_time: str = Field(default="1.[d]", description="End time with units")
    dt: str = Field(default="1.0[h]", description="Time step with units")
    soil_params_smcmax: float = Field(..., description="Maximum soil moisture content", alias="smcmax")
    soil_params_b: float = Field(..., description="Soil moisture retention curve parameter (bexp)", alias="b")
    soil_params_satpsi: float = Field(..., description="Saturated soil suction (psisat)", alias="satpsi")
    soil_params_quartz: float = Field(default=1.0, description="Quartz content", alias="quartz")
    ice_fraction_scheme: IceFractionScheme = Field(..., description="Ice fraction scheme")
    soil_z: list[float] = Field(default=[0.1, 0.3, 1.0, 2.0], description="Soil depth layers in meters")
    soil_temperature: list[float] = Field(..., description="Soil temperature in Kelvin for each layer")

    @field_validator("soil_temperature")
    @classmethod
    def validate_soil_temperature_length(cls, v, info):
        """Ensure soil_temperature has same length as soil_z"""
        # Get soil_z from the data being validated
        soil_z = info.data.get("soil_z", [0.1, 0.3, 1.0, 2.0])
        if len(v) != len(soil_z):
            raise ValueError(f"soil_temperature must have {len(soil_z)} values to match soil_z layers")
        return v

    def to_bmi_config(self) -> list[str]:
        """Convert the model back to the original config file format"""
        temp_values = ",".join([str(temp) for temp in self.soil_temperature])
        z_values = ",".join([str(z) for z in self.soil_z])

        return [
            f"verbosity={self.verbosity}",
            f"soil_moisture_bmi={self.soil_moisture_bmi}",
            f"end_time={self.end_time}",
            f"dt={self.dt}",
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
