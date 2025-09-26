from logging import Logger

from fastapi import HTTPException, Request
from pyiceberg.catalog import Catalog
from rustworkx import PyDiGraph


def get_logger(request: Request) -> Logger:
    """Gets the application logger from the app state"""
    if not hasattr(request.app.state, "catalog") or request.app.state.catalog is None:
        raise HTTPException(status_code=500, detail="Logger not loaded")
    return request.app.state.main_logger


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


def get_graphs(request: Request) -> PyDiGraph:
    """Gets the rustworkx graph objects from the app state

    Parameters
    ----------
    request : Request
        The FastAPI request object containing the application state

    Returns
    -------
    dict[str, rustworkx.PyDiGraph]
        A dictionary with all pydigraph objects

    Raises
    ------
    HTTPException
        If the catalog is not loaded or not available in the application state.
        Returns HTTP 500 status code with "Catalog not loaded" detail message.
    """
    if not hasattr(request.app.state, "network_graphs") or request.app.state.network_graphs is None:
        raise HTTPException(status_code=500, detail="network_graphs not loaded")
    return request.app.state.network_graphs
