from pyiceberg.catalog import Catalog, load_catalog


def get_catalog(_catalog: str = "glue") -> Catalog:
    """Gets the pyiceberg catalog reference"""
    return load_catalog(_catalog)
