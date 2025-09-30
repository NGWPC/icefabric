import os

from tqdm import tqdm

from icefabric.builds.icechunk_s3_module import IcechunkRepo
from icefabric.schemas.topobathy import NGWPCLocations


def convert_topobathy_to_tiff(output_dir: str, ic_rasters: list[str]) -> None:
    """Converts topobathy layers from icechunk to tiff for use in tiles

    Parameters
    ----------
    output_dir : str
        Directory to save outputs to
    ic_rasters : list[NGWPCLocations]
        list of NGWPCLocation raster paths. eg. [NGWPCLocations[TOPO_AK_30M_IC].path]
    """
    for ic_raster in tqdm(ic_rasters, desc="Downloading IC Rasters to .tif"):
        repo = IcechunkRepo(location=NGWPCLocations[ic_raster].path)
        output = os.path.join(output_dir, f"{str.split(str(NGWPCLocations[ic_raster].path), '/')[-1]}.tif")

        repo.retrieve_and_convert_to_tif(dest=output, var_name="elevation")
