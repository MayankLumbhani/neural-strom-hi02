"""FastAPI application factory."""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create the grievance API application."""
    return FastAPI(title="Neural Storm Grievance API")
