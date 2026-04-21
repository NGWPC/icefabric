import time
from pathlib import Path

from pyiceberg.catalog import load_catalog

from icefabric.helpers import load_creds
from icefabric.hydrofabric import subset_nhf

if __name__ == "__main__":
    load_creds()
    results = {"inmem": [], "sql": [], "glue": []}
    catalog_list = ["inmem", "sql", "glue"]
    gage_sel = ["01099500", "06858000", "10245800"]
    flowpath_sel = ["3764560", "1423906", "1581453"]
    for cat_name in catalog_list:
        catalog = load_catalog(cat_name)
        for fp in flowpath_sel:
            out_file = Path(f"/tmp/{fp}_{cat_name}.gpkg")

            print(f"Command ({cat_name}) starting...")
            start_time = time.perf_counter()
            subset_nhf(flowpath_id=fp, catalog=catalog, output=out_file)
            end_time = time.perf_counter()

            elapsed_time = end_time - start_time
            print(f"Command ({cat_name}) executed in {elapsed_time:.4f} seconds")
            results[cat_name].append(elapsed_time)
        for gage in gage_sel:
            out_file = Path(f"/tmp/{gage}_{cat_name}.gpkg")

            print(f"Command ({cat_name}) starting...")
            start_time = time.perf_counter()
            subset_nhf(gage_id=gage, catalog=catalog, output=out_file)
            end_time = time.perf_counter()

            elapsed_time = end_time - start_time
            print(f"Command ({cat_name}) executed in {elapsed_time:.4f} seconds")
            results[cat_name].append(elapsed_time)

    for r in results:
        avg = sum(results[r]) / len(results[r])
        print(f"{r} average - {avg:.4f} seconds")
