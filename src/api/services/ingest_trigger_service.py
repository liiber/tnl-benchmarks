import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime

from src.api.schemas.ingest_trigger import IngestStatusResponse, IngestTriggerResponse
from src.utils import utcnow

LOG_PATH = "/tmp/ingest-trigger.log"
APP_DIR = "/app"


@dataclass
class IngestRuntimeState:
    process: subprocess.Popen | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None


_state = IngestRuntimeState()
_lock = threading.Lock()


def _refresh_state() -> None:
    if _state.process is None:
        return
    exit_code = _state.process.poll()
    if exit_code is None:
        return
    _state.exit_code = exit_code
    _state.finished_at = _state.finished_at or utcnow()
    _state.process = None


def trigger_ingest(skip_prepare: bool) -> IngestTriggerResponse | None:
    with _lock:
        _refresh_state()
        if _state.process is not None:
            return None

        command = ["python", "-m", "src.scripts.ingest_run"]
        if skip_prepare:
            command.append("--skip-prepare")

        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=APP_DIR,
                start_new_session=True,
            )
        _state.process = process
        _state.started_at = utcnow()
        _state.finished_at = None
        _state.exit_code = None

        return IngestTriggerResponse(
            status="started",
            pid=process.pid,
            started_at=_state.started_at,
            log_path=LOG_PATH,
        )


def get_ingest_status() -> IngestStatusResponse:
    with _lock:
        _refresh_state()
        if _state.process is not None:
            return IngestStatusResponse(
                status="running",
                pid=_state.process.pid,
                started_at=_state.started_at,
                finished_at=None,
                exit_code=None,
                log_path=LOG_PATH,
            )

        if _state.started_at is None:
            return IngestStatusResponse(status="idle", log_path=LOG_PATH)

        status = "failed" if (_state.exit_code or 0) != 0 else "completed"
        return IngestStatusResponse(
            status=status,
            pid=None,
            started_at=_state.started_at,
            finished_at=_state.finished_at,
            exit_code=_state.exit_code,
            log_path=LOG_PATH,
        )


def cancel_ingest() -> bool:
    with _lock:
        _refresh_state()
        if _state.process is None:
            return False
        try:
            os.killpg(os.getpgid(_state.process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        _state.finished_at = utcnow()
        _state.exit_code = -signal.SIGTERM
        _state.process = None
        return True
