#!/usr/bin/env python
"""Crosswalk SCHISM mesh against an NGWPC Hydrofabric.

Constructs boundary lines from the SCHISM mesh (inland from NBOU, seaward from
NOPE), finds where hydrofabric flowpaths cross these lines flowing downstream
into the mesh, and maps each crossing to a boundary element.

Current version of this tool was built for NHF v1.1.3 and uses schism meshes in gr3 format.

An example schism mesh can be found at: s3://ngwpc-coastal/parm/coastal/atlgulf/hgrid.gr3
The full NHF gpkg for superCONUS can be found at: s3://edfs-data/hydrofabric-builds/super_conus/nhf_1.1.3.gpkg

Script produces two output sets:
  1. Inlets — flowpaths crossing the inland boundary (NBOU) flowing downstream.
  2. Seaward — flowpaths crossing the open boundary (NOPE) flowing downstream.

Each set is written as a CSV and a GPKG (with points and cell polygon layers).

Usage:
  python create_coastal_crosswalk.py hgrid.gr3 nhf_1.1.3.gpkg
  python create_coastal_crosswalk.py hgrid.gr3 nhf_1.1.3.gpkg --out-name my_crosswalk
"""

import argparse
import pathlib
from collections import defaultdict

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString
from sklearn.neighbors import BallTree


def buffer_to_dict(path):
    """Parse an hgrid.gr3 file into nodes, elements, and boundaries.

    Reuses the parsing logic from boundary_elements.py.
    """

    def first_el(line):
        return line.split(None, 1)[0].strip()

    buf = open(path)
    description = next(buf)
    rv = {"description": description}
    NE, NP = map(int, next(buf).split())
    nodes = np.loadtxt(buf, max_rows=NP)
    columns = ["x", "y", "z"][: nodes.shape[1] - 1]
    rv["nodes"] = pd.DataFrame(nodes[:, 1:], index=pd.Index(nodes[:, 0], dtype=int), columns=columns)
    rv["nodes"] = rv["nodes"].sort_index()

    elements = np.loadtxt(buf, dtype=int, max_rows=NE)
    rv["elements"] = pd.DataFrame(elements[:, 1:], index=pd.Index(elements[:, 0], dtype=int))
    rv["elements"] = rv["elements"].sort_index()

    # Parse open boundaries (NOPE)
    try:
        NOPE = int(next(buf).split()[0])
    except (IndexError, StopIteration):
        buf.close()
        return rv

    open_boundaries = []
    next(buf)
    for _ in range(NOPE):
        NETA = int(next(buf).split()[0])
        seg = [int(first_el(next(buf))) for _ in range(NETA)]
        open_boundaries.append(seg)
    rv["open_boundaries"] = open_boundaries

    # Parse land boundaries (NBOU)
    NBOU = int(next(buf).split()[0])
    buf.readline()
    land_boundaries = []
    for _ in range(NBOU):
        parts = next(buf).split()
        npts, ibtype = int(parts[0]), int(parts[1])
        seg = []
        for _ in range(npts):
            line = next(buf).split()
            seg.append(int(line[0]))
        land_boundaries.append((ibtype, seg))
    rv["land_boundaries"] = land_boundaries
    buf.close()
    return rv


def boundary_nodes_to_line(mesh, node_ids, target_crs):
    """Build a LineString from ordered boundary node IDs.

    Returns (line_in_target_crs, line_in_4326).
    """
    nodes_df = mesh["nodes"]
    coords = [(nodes_df.loc[n, "x"], nodes_df.loc[n, "y"]) for n in node_ids]
    line_4326 = LineString(coords)
    line_gdf = gpd.GeoDataFrame(geometry=[line_4326], crs="EPSG:4326")
    line_target = line_gdf.to_crs(target_crs).geometry.iloc[0]
    return line_target, line_4326


def build_nexus_lookup(nexus_gdf):
    """Build a dictionary mapping nex_id to Point geometry for O(1) lookups."""
    return dict(zip(nexus_gdf["nex_id"], nexus_gdf.geometry, strict=False))


def _cross_product_sign(px, py, ax, ay, bx, by):
    """Sign of cross product of (B-A) x (P-A)."""
    return (bx - ax) * (py - ay) - (by - ay) * (px - ax)


def is_on_mesh_side(px, py, seg_start, seg_end, elem_centroid):
    """Check if a point is on the same side of a boundary segment as the mesh interior.

    Uses the cross product to determine which side of the directed segment
    (seg_start -> seg_end) a point falls on, calibrated against elem_centroid
    which is known to be on the mesh-interior side.

    All coordinates must be in the same CRS.
    """
    sign_point = _cross_product_sign(px, py, *seg_start, *seg_end)
    sign_centroid = _cross_product_sign(elem_centroid[0], elem_centroid[1], *seg_start, *seg_end)
    return (sign_point > 0) == (sign_centroid > 0)


def get_boundary_context(cross_xy, bnd_ids, bnd_coords, node_to_elems, elem_centroids):
    """Get a local boundary segment and mesh element centroid near a crossing point.

    For the cross-product direction check, we need:
    1. Two adjacent boundary nodes forming the nearest segment
    2. A mesh element centroid on the interior side of that segment

    All coordinates must be in the same CRS.

    Parameters
    ----------
    cross_xy : tuple
        (x, y) of the crossing point.
    bnd_ids : ndarray
        Array of boundary node IDs.
    bnd_coords : ndarray
        (N, 2) array of boundary node (x, y) coordinates.
    node_to_elems : dict
        Mapping from node ID to list of element row indices.
    elem_centroids : dict
        Mapping from element row index to (cx, cy) centroid coordinates.

    Returns
    -------
    tuple or None
        ((seg_start_x, seg_start_y), (seg_end_x, seg_end_y), (cx, cy)) or None if
        no element centroid can be found.
    """
    dists = np.sqrt((bnd_coords[:, 0] - cross_xy[0]) ** 2 + (bnd_coords[:, 1] - cross_xy[1]) ** 2)
    nearest_idx = np.argsort(dists)[:2]
    n0, n1 = bnd_ids[nearest_idx[0]], bnd_ids[nearest_idx[1]]
    seg_start = tuple(bnd_coords[nearest_idx[0]])
    seg_end = tuple(bnd_coords[nearest_idx[1]])

    elem_rows = node_to_elems.get(n0, []) or node_to_elems.get(n1, [])
    if not elem_rows:
        return None

    for row_idx in elem_rows:
        if row_idx in elem_centroids:
            return seg_start, seg_end, elem_centroids[row_idx]

    return None


def enrich_with_hydrofabric(df, nexus, fp):
    """Merge flowpath and divide attributes onto a DataFrame with nex_id."""
    df = df.merge(
        nexus[["nex_id", "dn_fp_id"]].drop_duplicates(),
        on="nex_id",
        how="left",
    )
    df = df.merge(
        fp[["fp_id", "div_id"]].drop_duplicates(),
        left_on="dn_fp_id",
        right_on="fp_id",
        how="left",
    )
    return df


def write_outputs(results_df, boundary_line_4326, boundary_label, out_name):
    """Write CSV and GPKG (points + boundary line layers) for a result set."""
    out_csv = pathlib.Path.cwd() / f"{out_name}.csv"
    out_gpkg = pathlib.Path.cwd() / f"{out_name}.gpkg"

    # Point layer
    point_geom = gpd.points_from_xy(results_df["longitude"], results_df["latitude"])
    results_gdf = gpd.GeoDataFrame(results_df, geometry=point_geom, crs="EPSG:4326")

    # Boundary line layer
    line_gdf = gpd.GeoDataFrame(
        {"name": [boundary_label]},
        geometry=[boundary_line_4326],
        crs="EPSG:4326",
    )

    print(f"  Writing {out_csv}")
    results_gdf.drop(columns="geometry").to_csv(out_csv, index=False)
    print(f"  Writing {out_gpkg} (points + boundary)")
    results_gdf.to_file(out_gpkg, driver="GPKG", layer="points")
    line_gdf.to_file(out_gpkg, driver="GPKG", layer="boundary", mode="a")
    print(f"  {len(results_gdf)} records written")


def build_boundary_node_to_elem(boundary_node_ids, elements):
    """Build a node-to-element index for boundary nodes only.

    Instead of scanning all elements, inverts the element table: for each
    boundary node, finds which elements contain it.
    """
    bnd_set = set(boundary_node_ids)
    node_to_elems = defaultdict(list)
    elem_values = elements.values
    n_per_elem = elem_values[:, 0]
    node_cols = elem_values[:, 1:]

    # Only iterate elements that contain at least one boundary node
    # Use vectorized check first to find candidate rows
    max_cols = node_cols.shape[1]
    for col in range(max_cols):
        col_vals = node_cols[:, col]
        # Only check rows where this column is valid (col < n_per_elem)
        valid = col < n_per_elem
        for row_idx in np.where(valid & np.isin(col_vals, list(bnd_set)))[0]:
            nid = col_vals[row_idx]
            node_to_elems[nid].append(row_idx)

    return node_to_elems


def find_crossings(
    boundary_line,
    fp_gdf,
    nexus,
    boundary_node_ids,
    mesh,
    node_to_elems,
    max_distance_km,
    nexus_lookup=None,
    boundary_type="inlet",
):
    """Find flowpaths that cross a boundary line flowing downstream.

    Returns a DataFrame of crossing points matched to boundary elements.
    """
    earth_radius_km = 6371.0
    nodes_df = mesh["nodes"]
    elements = mesh["elements"]

    # Find flowpaths that intersect the boundary line
    # Both must be in the same CRS (use the flowpath CRS = hydrofabric CRS)
    crossing_mask = fp_gdf.geometry.intersects(boundary_line)
    crossing_fps = fp_gdf[crossing_mask].copy()

    if len(crossing_fps) == 0:
        return pd.DataFrame()

    print(f"  {len(crossing_fps)} flowpaths cross the boundary line")

    # Pre-compute boundary node coords and element centroids in hydrofabric CRS
    # so that direction checks don't need per-flowpath reprojection
    bnd_arr = np.array(boundary_node_ids)
    bnd_pts_gdf = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(nodes_df.loc[bnd_arr, "x"], nodes_df.loc[bnd_arr, "y"]),
        crs="EPSG:4326",
    ).to_crs(fp_gdf.crs)
    bnd_coords_hf = np.column_stack([bnd_pts_gdf.geometry.x, bnd_pts_gdf.geometry.y])

    unique_elem_rows = set()
    for nid in bnd_arr:
        unique_elem_rows.update(node_to_elems.get(nid, []))

    centroids_x, centroids_y, centroid_rows = [], [], []
    for row_idx in unique_elem_rows:
        n_nodes = elements.values[row_idx, 0]
        nids = elements.values[row_idx, 1 : n_nodes + 1]
        centroids_x.append(nodes_df.loc[nids, "x"].mean())
        centroids_y.append(nodes_df.loc[nids, "y"].mean())
        centroid_rows.append(row_idx)

    elem_centroids_hf = {}
    if centroid_rows:
        ec_gdf = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy(centroids_x, centroids_y),
            crs="EPSG:4326",
        ).to_crs(fp_gdf.crs)
        elem_centroids_hf = {
            centroid_rows[i]: (ec_gdf.geometry.iloc[i].x, ec_gdf.geometry.iloc[i].y)
            for i in range(len(centroid_rows))
        }

    # For each crossing flowpath, verify straddle + flow direction, then get intersection point
    results = []
    skipped_direction = 0
    for _, row in crossing_fps.iterrows():
        # Step 1: Geometric straddle check — start/end of geometry on opposite sides
        line = row.geometry.geoms[0] if row.geometry.geom_type == "MultiLineString" else row.geometry
        start_pt = line.coords[0]
        end_pt = line.coords[-1]
        nexus_line = LineString([start_pt, end_pt])
        if not nexus_line.intersects(boundary_line):
            continue

        # Step 2: Direction check using nexus points + cross product
        if nexus_lookup is not None:
            up_nex = row.up_nex_id if hasattr(row, "up_nex_id") else np.nan
            dn_nex = row.dn_nex_id if hasattr(row, "dn_nex_id") else np.nan

            up_pt = nexus_lookup.get(int(up_nex)) if pd.notna(up_nex) else None
            dn_pt = nexus_lookup.get(int(dn_nex)) if pd.notna(dn_nex) else None

            # Resolve upstream/downstream coordinates for the direction check
            if up_pt is not None and dn_pt is not None:
                up_x, up_y = up_pt.x, up_pt.y
                dn_x, dn_y = dn_pt.x, dn_pt.y
            elif up_pt is None and dn_pt is not None:
                # Headwater: use the flowpath endpoint farthest from dn_nex as upstream
                dn_x, dn_y = dn_pt.x, dn_pt.y
                d_start = (start_pt[0] - dn_x) ** 2 + (start_pt[1] - dn_y) ** 2
                d_end = (end_pt[0] - dn_x) ** 2 + (end_pt[1] - dn_y) ** 2
                up_x, up_y = (start_pt[0], start_pt[1]) if d_start >= d_end else (end_pt[0], end_pt[1])
            else:
                up_x = up_y = dn_x = dn_y = None

            if up_x is not None:
                mid_x = (start_pt[0] + end_pt[0]) / 2
                mid_y = (start_pt[1] + end_pt[1]) / 2

                ctx = get_boundary_context(
                    (mid_x, mid_y), bnd_arr, bnd_coords_hf, node_to_elems, elem_centroids_hf
                )
                if ctx is not None:
                    seg_start, seg_end, elem_centroid = ctx

                    up_mesh = is_on_mesh_side(up_x, up_y, seg_start, seg_end, elem_centroid)
                    dn_mesh = is_on_mesh_side(dn_x, dn_y, seg_start, seg_end, elem_centroid)

                    if boundary_type == "inlet":
                        # Inlet: up_nex outside mesh (inland), dn_nex inside mesh (coastal)
                        if up_mesh or not dn_mesh:
                            skipped_direction += 1
                            continue
                    elif boundary_type == "seaward":
                        # Seaward: up_nex inside mesh, dn_nex outside mesh
                        if not up_mesh or dn_mesh:
                            skipped_direction += 1
                            continue

        # Step 3: Compute intersection point
        intersection = row.geometry.intersection(boundary_line)
        if intersection.is_empty:
            continue

        if intersection.geom_type == "Point":
            cross_pt = intersection
        elif intersection.geom_type == "MultiPoint":
            cross_pt = intersection.geoms[0]
        else:
            # LineString overlap or GeometryCollection — take centroid
            cross_pt = intersection.centroid

        results.append(
            {
                "fp_id": row.fp_id,
                "dn_nex_id": row.dn_nex_id,
                "cross_x": cross_pt.x,
                "cross_y": cross_pt.y,
            }
        )

    if not results:
        return pd.DataFrame()

    if skipped_direction > 0:
        print(f"  Skipped {skipped_direction} flowpaths with wrong flow direction")

    crossings_df = pd.DataFrame(results)
    print(f"  {len(crossings_df)} downstream crossings")

    # Get the downstream nexus for each crossing
    crossings_df["dn_nex_id"] = crossings_df["dn_nex_id"].astype("Int64")
    crossings_df = crossings_df.merge(
        nexus[["nex_id"]],
        left_on="dn_nex_id",
        right_on="nex_id",
        how="left",
    )

    # Match crossing points to nearest boundary element using BallTree
    # Convert boundary nodes to (lat, lon) radians for haversine
    boundary_arr = np.array(boundary_node_ids)
    bnd_coords = nodes_df.loc[boundary_arr, ["y", "x"]].values  # lat, lon
    bnd_rad = np.deg2rad(bnd_coords)
    bnd_tree = BallTree(bnd_rad, metric="haversine")

    # Reproject crossing points to EPSG:4326
    cross_gdf = gpd.GeoDataFrame(
        crossings_df,
        geometry=gpd.points_from_xy(crossings_df["cross_x"], crossings_df["cross_y"]),
        crs=fp_gdf.crs,
    ).to_crs("EPSG:4326")

    cross_rad = np.deg2rad(np.column_stack([cross_gdf.geometry.y, cross_gdf.geometry.x]))

    dist, idxs = bnd_tree.query(cross_rad, k=2)
    dist_km = dist[:, 0] * earth_radius_km

    # Discard matches where the nearest boundary node is farther than max_distance_km
    close_mask = dist_km <= max_distance_km
    if not close_mask.any():
        return pd.DataFrame()

    # Find boundary elements from 2 nearest boundary nodes
    element_nodes = boundary_arr[idxs]
    all_elements = elements.values[:, 1:]
    all_element_ids = elements.index.values
    all_n_per_elem = elements.values[:, 0]

    out_rows = []
    close_indices = np.where(close_mask)[0]
    for idx in close_indices:
        n0, n1 = element_nodes[idx]
        elems_0 = set(node_to_elems.get(n0, []))
        elems_1 = set(node_to_elems.get(n1, []))
        common = elems_0 & elems_1
        if common:
            row_idx = min(common)
        elif elems_0 or elems_1:
            row_idx = min(elems_0 | elems_1)
        else:
            continue

        elem_id = all_element_ids[row_idx]
        n = all_n_per_elem[row_idx]
        nids = all_elements[row_idx, :n]
        centroid_lon = nodes_df.loc[nids, "x"].mean()
        centroid_lat = nodes_df.loc[nids, "y"].mean()

        row_data = crossings_df.iloc[idx]
        out_rows.append(
            {
                "element_id": elem_id,
                "fp_id": row_data["fp_id"],
                "nex_id": row_data.get("nex_id", np.nan),
                "longitude": centroid_lon,
                "latitude": centroid_lat,
                "distance_km": dist_km[idx],
            }
        )

    result = pd.DataFrame(out_rows)
    if len(result) == 0:
        return result

    # One element per flowpath/divide: keep the closest crossing per fp_id
    n_before = len(result)
    result = result.sort_values("distance_km").drop_duplicates("fp_id", keep="first")
    if len(result) < n_before:
        print(f"  Deduplicated {n_before} -> {len(result)} (one element per flowpath)")

    return result


def get_options():
    """Parse command-line arguments for the coastal crosswalk tool."""
    parser = argparse.ArgumentParser(description="Crosswalk SCHISM mesh against an NGWPC Hydrofabric")
    parser.add_argument("grid", type=pathlib.Path, help="Path to hgrid.gr3")
    parser.add_argument("gpkg", type=pathlib.Path, help="Path to hydrofabric .gpkg")
    parser.add_argument(
        "--out-name",
        default="schism_hydrofabric_crosswalk",
        type=str,
        help="Base name prefix for output files (default: schism_hydrofabric_crosswalk)",
    )
    parser.add_argument(
        "--max-distance-km",
        default=5.0,
        type=float,
        help="Discard matches farther than this (default: 5 km)",
    )
    return parser.parse_args()


def main():
    """Crosswalk a SCHISM mesh against an NGWPC Hydrofabric."""
    args = get_options()

    print("Reading hydrofabric nexus points...")
    nexus = gpd.read_file(args.gpkg, layer="nexus")
    hf_crs = nexus.crs
    print(f"  {len(nexus)} nexus points loaded (CRS: {hf_crs})")

    print("Reading hydrofabric flowpaths...")
    fp = gpd.read_file(args.gpkg, layer="flowpaths")
    print(f"  {len(fp)} flowpaths loaded")

    print("Reading SCHISM mesh (this may take a while for large grids)...")
    mesh = buffer_to_dict(args.grid)
    nodes_df = mesh["nodes"]
    elements = mesh["elements"]
    print(f"  {len(elements)} elements, {len(nodes_df)} nodes")

    print("Building boundary lines...")

    # Inland boundary
    land_nodes = []
    for _, seg in mesh["land_boundaries"]:
        land_nodes.extend(seg)
    inland_line, inland_line_4326 = boundary_nodes_to_line(mesh, land_nodes, hf_crs)
    print(f"  Inland boundary: {len(land_nodes)} nodes")

    # Seaward boundary
    open_nodes = []
    for seg in mesh["open_boundaries"]:
        open_nodes.extend(seg)
    seaward_line, seaward_line_4326 = boundary_nodes_to_line(mesh, open_nodes, hf_crs)
    print(f"  Seaward boundary: {len(open_nodes)} nodes")

    all_bnd_nodes = land_nodes + open_nodes
    print(f"Building node-to-element index for {len(all_bnd_nodes)} boundary nodes...")
    node_to_elems = build_boundary_node_to_elem(all_bnd_nodes, elements)
    print(f"  Indexed {len(node_to_elems)} boundary nodes across elements")

    print("Building nexus lookup...")
    nexus_lookup = build_nexus_lookup(nexus)
    print(f"  {len(nexus_lookup)} nexus entries")

    print("\n=== Inlets (flowpaths crossing inland boundary downstream) ===")
    inlets_df = find_crossings(
        inland_line,
        fp,
        nexus,
        land_nodes,
        mesh,
        node_to_elems,
        args.max_distance_km,
        nexus_lookup=nexus_lookup,
        boundary_type="inlet",
    )

    if len(inlets_df) > 0:
        inlets_df = enrich_with_hydrofabric(inlets_df, nexus, fp)
        write_outputs(
            inlets_df,
            inland_line_4326,
            "inland_boundary",
            f"{args.out_name}_inlets",
        )
    else:
        print("  No inlet crossings found.")

    print("\n=== Seaward (flowpaths crossing open boundary downstream) ===")
    seaward_df = find_crossings(
        seaward_line,
        fp,
        nexus,
        open_nodes,
        mesh,
        node_to_elems,
        args.max_distance_km,
        nexus_lookup=nexus_lookup,
        boundary_type="seaward",
    )

    if len(seaward_df) > 0:
        seaward_df = enrich_with_hydrofabric(seaward_df, nexus, fp)
        write_outputs(
            seaward_df,
            seaward_line_4326,
            "seaward_boundary",
            f"{args.out_name}_seaward",
        )
    else:
        print("  No seaward crossings found.")

    print("\nDone.")


if __name__ == "__main__":
    main()
