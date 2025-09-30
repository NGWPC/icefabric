from fastapi import HTTPException, Request
from pyiceberg.catalog import Catalog


def get_catalog(request: Request) -> Catalog:
    """Gets the pyiceberg catalog reference from the app state

    Parameters
    ----------
    request : Request
        The FastAPI request object containing the application state

    Returns
    -------
    pyiceberg.catalog.Catalog
        The loaded pyiceberg catalog instance used for querying versioned EDFS data

    Raises
    ------
    HTTPException
        If the catalog is not loaded or not available in the application state.
        Returns HTTP 500 status code with "Catalog not loaded" detail message.
    """
    if not hasattr(request.app.state, "catalog") or request.app.state.catalog is None:
        raise HTTPException(status_code=500, detail="Catalog not loaded")
    return request.app.state.catalog
