import json
import time
from pathlib import Path
from typing import Any
from urllib import request

DEBUG_LOG_PATH = Path(__file__).resolve().parents[2] / "debug-9a0089.log"
SESSION_ID = "9a0089"
INGEST_ENDPOINT = "http://127.0.0.1:7846/ingest/e1674615-b504-4fd4-8f3a-1565d91c124e"

def write_debug_log(*, run_id: str, hypothesis_id: str, location: str, message: str, data: dict[str, Any]) -> None:
    payload = {
        "sessionId": SESSION_ID,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
        "location": location,
        "message": message,
        "data": data,
        "timestamp": int(time.time() * 1000),
    }
    try:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        req = request.Request(
            INGEST_ENDPOINT,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Debug-Session-Id": SESSION_ID,
            },
            method="POST",
        )
        request.urlopen(req, timeout=1.0).read()
    except Exception:
        pass

    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass
