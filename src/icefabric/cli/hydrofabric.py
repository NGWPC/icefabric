"""Contains all click CLI code for the hydrofabric"""

import json
from pathlib import Path

import click
import geopandas as gpd

from icefabric.builds import build_upstream_json
from icefabric.cli import get_catalog
from icefabric.hydrofabric.subset import subset_hydrofabric
from icefabric.schemas.hydrofabric import HydrofabricDomains, IdType


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

    # Create or load upstream lookup table
    upstream_connections_path = (
        Path(__file__).parents[3] / f"data/hydrofabric/{domain}_upstream_connections.json"
    )
    assert upstream_connections_path.exists(), (
        f"Upstream Connections missing for {domain}. Please run `icefabric build-upstream-connections` to generate this file"
    )

    with open(upstream_connections_path) as f:
        data = json.load(f)
        print(
            f"Loading upstream connections connected generated on: {data['_metadata']['generated_at']} from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
        )
        upstream_dict = data["upstream_connections"]

    layers_list = list(layers) if layers else ["divides", "flowpaths", "network", "nexus"]

    output_layers = subset_hydrofabric(
        catalog=get_catalog(catalog),
        identifier=identifier,
        id_type=id_type_enum,
        layers=layers_list,
        namespace=domain,
        upstream_dict=upstream_dict,
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file:
        for table_name, _layer in output_layers.items():
            if len(_layer) > 0:  # Only save non-empty layers
                gpd.GeoDataFrame(_layer).to_file(output_file, layer=table_name, driver="GPKG")
            else:
                print(f"Warning: {table_name} layer is empty")

    click.echo(f"Hydrofabric file created successfully in the following folder: {output_file}")


@click.command()
@click.option(
    "--catalog",
    type=click.Choice(["glue", "sql"], case_sensitive=False),
    default="glue",
    help="The pyiceberg catalog type",
)
@click.option(
    "--domain",
    type=click.Choice([e.value for e in HydrofabricDomains], case_sensitive=False),
    required=True,
    help="The domain you are querying",
)
@click.option(
    "--output-path",
    "-o",
    type=click.Path(path_type=Path),
    default=Path.cwd(),
    help="Output path of the upstream connections json",
)
def build_upstream_connections(
    catalog: str,
    domain: str,
    output_path: Path,
):
    """Creates a JSON file which documents the upstream connections from a particular basin"""
    build_upstream_json(catalog=get_catalog(catalog), namespace=domain, output_path=output_path)
    click.echo(f"Upstream json file created for {domain} in the following folder: {output_path}")
