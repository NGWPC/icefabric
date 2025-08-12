"""Helper functions designed to assist with managing data. Similar to util functions"""

import json
from pathlib import Path

from .origin import find_origin
from .subset import subset_hydrofabric


def load_upstream_connections(domain_val):
    """Helper function to generate the upstream_dict used in parameter generation"""
    try:
        # Load upstream connections (same as CLI)
        upstream_connections_path = (
            Path(__file__).parents[3] / f"data/hydrofabric/{domain_val}_upstream_connections.json"
        )

        if not upstream_connections_path.exists():
            raise FileNotFoundError(
                f"Upstream connections missing for {domain_val}. Please run `icefabric build-upstream-connections` to generate this file"
            )

        with open(upstream_connections_path) as f:
            data = json.load(f)
            print(
                f"Loading upstream connections generated on: {data['_metadata']['generated_at']} "
                f"from snapshot id: {data['_metadata']['iceberg']['snapshot_id']}"
            )
            upstream_dict = data["upstream_connections"]
    except FileNotFoundError:
        raise
    return upstream_dict


__all__ = ["find_origin", "load_upstream_connections", "subset_hydrofabric"]
