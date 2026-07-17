from fastapi import FastAPI

from src.api.routers.ingest_control import router as ingest_control_router
from src.api.routers.regression import router as regression_router
from src.api.routers.results import router as results_router


def create_app() -> FastAPI:
    app = FastAPI(title="TNL Benchmarks API", version="1.0.0")
    app.include_router(results_router)
    app.include_router(regression_router)
    app.include_router(ingest_control_router)
    return app


app = create_app()
