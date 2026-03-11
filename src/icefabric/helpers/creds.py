"""A file for cred helpers"""

import os

from dotenv import load_dotenv
from pyprojroot import here


def load_creds(deploy: str | None = "test"):
    """Loads the .env and .pyiceberg.yaml files from the project root

    Parameters
    ----------
    dir : Path
        The directory where the creds exist

    Raises
    ------
    FileNotFoundError
        The .pyiceberg.yaml file does not exist
    """
    if deploy.lower() in ["t", "test"]:
        load_dotenv(dotenv_path=here() / ".env", override=True)
        os.environ["CATALOG_S3_BUCKET"] = "edfs-data"
    elif deploy.lower() in ["p", "prod", "production", "oe"]:
        load_dotenv(dotenv_path=here() / ".prod.env", override=True)
        os.environ["CATALOG_S3_BUCKET"] = "iceberg-data-oe"
    pyiceberg_file = here() / ".pyiceberg.yaml"
    if pyiceberg_file.exists():
        os.environ["PYICEBERG_HOME"] = str(pyiceberg_file)
    else:
        raise FileNotFoundError(
            "Cannot find .pyiceberg.yaml. Please download this from NGWPC confluence or create "
        )
