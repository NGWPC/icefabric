"""Contains all click CLI code for NWM modules"""

from pathlib import Path

import click

from icefabric._version import __version__
from icefabric.cli import get_catalog
from icefabric.helpers.io import _create_config_zip
from icefabric.modules import NWMModules, config_mapper
from icefabric.schemas.hydrofabric import HydrofabricDomains
from icefabric.schemas.modules import IceFractionScheme


@click.command()
@click.option(
    "--gauge",
    type=str,
    help="The Gauge ID to subset the Hydrofabric from and get upstream catchment information",
)
@click.option(
    "--module",
    type=click.Choice([module.value for module in NWMModules], case_sensitive=False),
    help="The module to create initial parameter config files for",
)
@click.option(
    "--domain",
    type=click.Choice([domain.name.lower() for domain in HydrofabricDomains], case_sensitive=False),
    help="The domain at which you are running your model",
)
@click.option(
    "--catalog",
    type=click.Choice(["glue", "sql"], case_sensitive=False),
    default="glue",
    help="The pyiceberg catalog type",
)
@click.option(
    "--ice-fraction",
    type=click.Choice(IceFractionScheme, case_sensitive=False),
    help="The ice fraction scheme used. Defaults to False to use Xinanjiang",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Output path for the zip file. Defaults to current directory",
)
def params(
    gauge: str,
    module: str,
    domain: HydrofabricDomains,
    catalog: str,
    ice_fraction: IceFractionScheme,
    output: Path,
):
    """Returns a zip file containing all config files requested by a specific module"""
    get_param_func = config_mapper[module]
    domain_enum = HydrofabricDomains[domain.upper()]
    ice_fraction_enum = (
        IceFractionScheme[ice_fraction.upper()] if ice_fraction else IceFractionScheme.XINANJIANG
    )  # Defaults to Xinanjiang

    configs = get_param_func(
        catalog=get_catalog(catalog),
        domain=domain_enum,
        identifier=gauge,
        use_schaake=True if ice_fraction_enum == IceFractionScheme.SCHAAKE else False,
    )

    output.parent.mkdir(parents=True, exist_ok=True)

    _create_config_zip(
        configs=configs,
        output_path=output,
        kwargs={
            "gauge_id": gauge,
            "domain": domain,
            "version": __version__,
            "module": module,
            "catalog_type": catalog,
            "ice_fraction": ice_fraction_enum.value,
        },
    )

    click.echo(f"Config files created successfully in the following folder: {output}")
