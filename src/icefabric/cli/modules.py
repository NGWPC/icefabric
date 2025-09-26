"""Contains all click CLI code for NWM modules"""

from pathlib import Path

import click
from dotenv import load_dotenv
from pyprojroot import here

from icefabric._version import __version__
from icefabric.builds.graph_connectivity import load_upstream_json
from icefabric.cli import get_catalog
from icefabric.helpers.io import _create_config_zip
from icefabric.modules import NWMModules, SmpModules, config_mapper, modules_with_extra_args
from icefabric.schemas.hydrofabric import HydrofabricDomains
from icefabric.schemas.modules import IceFractionScheme

load_dotenv()


def validate_options(ctx, param, value):
    """Validates options are only used with their respective modules"""
    if value is not None:
        module_choice = ctx.params.get("nwm_module")
        try:
            if param.name not in modules_with_extra_args[module_choice]:
                raise click.BadParameter(
                    f"'{param.opts[0]}' is inappropriate for the '{module_choice}' module."
                )
        except KeyError as err:
            raise KeyError(
                f"The '{module_choice}' module can't be used with non-standard (gage id, domain, etc.) arguments."
            ) from err
        return value


@click.command()
@click.option(
    "--gauge",
    type=str,
    help="The Gauge ID to subset the Hydrofabric from and get upstream catchment information",
)
@click.option(
    "--nwm-module",
    "nwm_module",
    type=click.Choice([module.value for module in NWMModules], case_sensitive=False),
    help="The module to create initial parameter config files for",
)
@click.option(
    "--domain",
    type=click.Choice([e.value for e in HydrofabricDomains], case_sensitive=False),
    required=True,
    help="The domain you are querying",
)
@click.option(
    "--catalog",
    type=click.Choice(["glue", "sql"], case_sensitive=False),
    default="glue",
    help="The pyiceberg catalog type",
)
@click.option(
    "--ice-fraction",
    "use_schaake",
    type=click.Choice(IceFractionScheme, case_sensitive=False),
    default=None,
    help="(SFT only) - The ice fraction scheme used. Defaults to False to use Xinanjiang",
    callback=validate_options,
)
@click.option(
    "--envca",
    type=bool,
    default=None,
    help="(Snow-17/SAC-SMA only) - If source is ENVCA, then set to True. Defaults to False.",
    callback=validate_options,
)
@click.option(
    "--smp-extra-module",
    "extra_module",
    type=click.Choice(SmpModules, case_sensitive=False),
    default=None,
    help="(SMP only) - Name of another module to be used alongisde SMP to fill out additional parameters.",
    callback=validate_options,
)
@click.option(
    "--cfe-version",
    "cfe_version",
    type=click.Choice(["CFE-X", "CFE-S"], case_sensitive=False),
    default=None,
    help="the CFE module type (e.g. CFE-X, CFE-S) for which determines whether to use Shaake or Xinanjiang for surface partitioning.",
    callback=validate_options,
)
@click.option(
    "--sft-included",
    type=bool,
    default=None,
    help='(LASAM only) - Denotes that SFT is in the "dep_modules_included" definition as declared in the HF API repo',
    callback=validate_options,
)
@click.option(
    "--soil-params-file",
    type=str,
    default=None,
    help="(LASAM only) - Name of the Van Genuchton soil parameters file",
    callback=validate_options,
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
    nwm_module: str,
    domain: str,
    catalog: str,
    use_schaake: IceFractionScheme,
    envca: bool,
    extra_module: SmpModules,
    sft_included: bool,
    cfe_version: str,
    soil_params_file: str,
    output: Path,
):
    """Returns a zip file containing all config files requested by a specific module"""
    # TODO - Remove the below if statement once topoflow has IPE/BMI generation
    if nwm_module == "topoflow":
        raise NotImplementedError("Topoflow not implemented yet")

    ice_fraction_enum = (
        IceFractionScheme[use_schaake.upper()] if use_schaake else IceFractionScheme.XINANJIANG
    )  # Defaults to Xinanjiang
    use_schaake = True if use_schaake == IceFractionScheme.SCHAAKE else False
    _catalog = get_catalog(catalog)
    graph = load_upstream_json(
        catalog=_catalog,
        namespaces=[domain],
        output_path=here() / "data",
    )[domain]

    ipe_kwargs = {}
    ipe_kwargs["catalog"] = _catalog
    ipe_kwargs["namespace"] = domain
    ipe_kwargs["identifier"] = f"gages-{gauge}"
    ipe_kwargs["graph"] = graph

    if nwm_module in modules_with_extra_args:
        for extra_arg in modules_with_extra_args[nwm_module]:
            if locals()[extra_arg] is not None:
                ipe_kwargs[extra_arg] = locals()[extra_arg]

    get_param_func = config_mapper[nwm_module]
    configs = get_param_func(**ipe_kwargs)

    output.parent.mkdir(parents=True, exist_ok=True)

    zip_metadata_kwargs = {
        "gauge_id": gauge,
        "domain": domain,
        "version": __version__,
        "module": nwm_module,
        "catalog_type": catalog,
    }
    if nwm_module == "sft":
        zip_metadata_kwargs["ice_fraction"] = ice_fraction_enum.value

    _create_config_zip(
        configs=configs,
        output_path=output,
        kwargs=zip_metadata_kwargs,
    )

    click.echo(f"Config files created successfully in the following folder: {output}")
