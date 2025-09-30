"""Contains all click CLI code for the hydrofabric"""

from pathlib import Path

import click
import geopandas as gpd

from icefabric.builds.graph_connectivity import load_upstream_json
from icefabric.cli import get_catalog
from icefabric.helpers import load_creds
from icefabric.hydrofabric.subset import subset_hydrofabric
from icefabric.schemas.hydrofabric import HydrofabricDomains, IdType

load_creds(dir=Path(__file__).parents[3])


@click.command()
@click.option(
    "--catalog",
    type=click.Choice(["glue", "sql"], case_sensitive=False),
    default="glue",
    help="The pyiceberg catalog type",
)
@click.option(
    "--identifier",
    type=str,
    required=True,
    help="The specific ID you are querying the system from",
)
@click.option(
    "--id-type",
    type=click.Choice([e.value for e in IdType], case_sensitive=False),
    required=True,
    help="The ID type you are querying",
)
@click.option(
    "--domain",
    type=click.Choice([e.value for e in HydrofabricDomains], case_sensitive=False),
    required=True,
    help="The domain you are querying",
)
@click.option(
    "--layers",
    multiple=True,
    default=["divides", "flowpaths", "network", "nexus"],
    help="The layers to include in the geopackage. Will always include ['divides', 'flowpaths', 'network', 'nexus']",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default=Path.cwd() / "subset.gpkg",
    help="Output file. Defaults to ${CWD}/subset.gpkg",
)
def subset(
    catalog: str,
    identifier: str,
    id_type: str,
    domain: str,
    layers: tuple[str],
    output_file: Path,
):
    """Subsets the hydrofabric based on a unique identifier"""
    id_type_enum = IdType(id_type)
    _catalog = get_catalog(catalog)

    connectivity_graphs = load_upstream_json(
        catalog=_catalog,
        namespaces=[domain],
        output_path=Path(__file__).parents[3] / "data",
    )

    layers_list = list(layers) if layers else ["divides", "flowpaths", "network", "nexus"]

    output_layers = subset_hydrofabric(
        catalog=_catalog,
        identifier=identifier,
        id_type=id_type_enum,
        layers=layers_list,
        namespace=domain,
        graph=connectivity_graphs[domain],
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file:
        for table_name, _layer in output_layers.items():
            if len(_layer) > 0:  # Only save non-empty layers
                gpd.GeoDataFrame(_layer).to_file(output_file, layer=table_name, driver="GPKG")
            else:
                print(f"Warning: {table_name} layer is empty")

    click.echo(f"Hydrofabric file created successfully in the following folder: {output_file}")
