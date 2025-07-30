#!/usr/bin/env python3
"""Main CLI entry point for icefabric"""

import click

from icefabric import __version__
from icefabric.cli.hydrofabric import build_upstream_connections, subset
from icefabric.cli.modules import params


def get_version():
    """Get the version of the icefabric package."""
    return __version__


@click.group()
@click.version_option(version=get_version())
@click.pass_context
def cli(ctx):
    """
    Ice fabric tools and utilities.

    A comprehensive toolkit for working with ice fabric data,
    hydrofabric processing, and related geospatial operations.
    """
    ctx.ensure_object(dict)


# Add subcommands
cli.add_command(params)
cli.add_command(subset)
cli.add_command(build_upstream_connections)

# Main entry point for when run as a script
if __name__ == "__main__":
    cli()
