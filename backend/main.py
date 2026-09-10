"""FastAPI application entry point for MarkoWizard web service."""

import logging
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .router import router

logger = logging.getLogger(__name__)

try:
    _VERSION = version("markowizard")
except PackageNotFoundError:  # pragma: no cover
    _VERSION = "0.0.0"

# Path to the frontend directory (relative to this file)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="MarkoWizard",
        description="Markowitz portfolio optimization and analysis API",
        version=_VERSION,
    )

    # CORS — allow all origins for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API router
    app.include_router(router, prefix="/api")

    # Serve static frontend files
    if FRONTEND_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
        logger.info("Serving frontend from %s", FRONTEND_DIR)
    else:
        logger.warning("Frontend directory not found at %s", FRONTEND_DIR)

    return app


app = create_app()


def run() -> None:
    """Entry point for the `markowizard-web` console script."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
