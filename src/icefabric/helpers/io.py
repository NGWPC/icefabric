import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml
from tqdm import tqdm

from icefabric.schemas.modules import NWMProtocol


def _create_config_zip(configs: list[NWMProtocol], output_path: Path, **kwargs):
    """Creates a zip file of BMI configs with a metadata.json file containing query information

    Parameters
    ----------
    configs : list[NWMProtocol]
        The list of config NWMProtocol models
    output_path : Path
        The output path location to write zip files
    """
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        config_files = []

        # Write config files
        for config in tqdm(configs, desc="Creating a config file", total=len(configs), ncols=140):
            file_path = config.model_dump_config(temp_dir)
            config_files.append(file_path)

        # Create metadata file
        metadata_path = temp_dir / "metadata.json"
        with metadata_path.open("w", encoding="UTF-8") as f:
            json.dump(kwargs["kwargs"], f)  # Removes the root from the dict
        config_files.append(metadata_path)

        output_file = output_path / "configs.zip"

        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as f:
            for file_path in config_files:
                archive_name = file_path.name
                f.write(file_path, archive_name)


def load_pyiceberg_config(cwd: Path) -> dict[str, Any]:
    """Reads a .pyiceberg.yaml config file to memory

    Parameters
    ----------
    cwd : Path
        the path to the .pyiceberg.yaml file

    Returns
    -------
    dict[str, Any]
        The pyiceberg yaml file

    Raises
    ------
    FileNotFoundError
        Can't find the YAML file in the CWD
    yaml.YAMLError
        Error parsing the YAML file
    """
    try:
        with open(cwd / ".pyiceberg.yaml", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data if data is not None else {}
    except FileNotFoundError as e:
        raise FileNotFoundError(f".pyiceberg YAML file not found in cwd: {cwd}") from e
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing .pyiceberg YAML file: {e}") from e
