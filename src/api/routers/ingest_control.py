from fastapi import APIRouter, Header, HTTPException

from src.api.schemas.ingest_trigger import (
    IngestStatusResponse,
    IngestTriggerRequest,
    IngestTriggerResponse,
)
from src.api.services.ingest_trigger_service import (
    cancel_ingest,
    get_ingest_status,
    trigger_ingest,
)
from src.environment import ENV

router = APIRouter(prefix="/api/v1/ingest", tags=["ingest-control"])


def _authorize(token: str | None) -> None:
    if ENV.INGEST_TRIGGER_TOKEN is None:
        return
    if token != ENV.INGEST_TRIGGER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid ingest trigger token.")


@router.post("/trigger", response_model=IngestTriggerResponse)
async def trigger_ingest_run(
    request: IngestTriggerRequest,
    x_ingest_token: str | None = Header(default=None, alias="X-Ingest-Token"),
) -> IngestTriggerResponse:
    _authorize(x_ingest_token)
    response = trigger_ingest(skip_prepare=request.skip_prepare)
    if response is None:
        raise HTTPException(status_code=409, detail="Ingest job is already running.")
    return response


@router.get("/status", response_model=IngestStatusResponse)
async def get_ingest_run_status(
    x_ingest_token: str | None = Header(default=None, alias="X-Ingest-Token"),
) -> IngestStatusResponse:
    _authorize(x_ingest_token)
    return get_ingest_status()


@router.post("/cancel", status_code=200)
async def cancel_ingest_run(
    x_ingest_token: str | None = Header(default=None, alias="X-Ingest-Token"),
) -> dict:
    _authorize(x_ingest_token)
    if not cancel_ingest():
        raise HTTPException(
            status_code=409, detail="No ingest job is currently running."
        )
    return {"status": "cancelled"}
