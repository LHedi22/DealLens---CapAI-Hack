from collections import deque
import time

log_store: deque = deque(maxlen=500)


def _blank_step() -> dict:
    return {
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "result_summary": None,
        "error": None,
    }


def _blank_pipeline() -> dict:
    return {
        "active": False,
        "startup_name": None,
        "started_at": None,
        "steps": {
            "extraction":   _blank_step(),
            "business":     _blank_step(),
            "esg":          _blank_step(),
            "memory":       _blank_step(),
            "forecasting":  _blank_step(),
            "fix_analysis": _blank_step(),
            "portfolio":    _blank_step(),
            "aggregator":   _blank_step(),
        },
        "raw_text": None,
        "ollama_calls": [],
        "final_result": None,
        "completed_at": None,
    }


pipeline_state: dict = _blank_pipeline()


# ── Logging ───────────────────────────────────────────────────────────────────

def emit_log(level: str, source: str, message: str, detail: dict | None = None) -> None:
    try:
        entry = {
            "id": str(time.time_ns()),
            "ts": time.time(),                      # numeric — Debug.jsx uses log.ts * 1000
            "timestamp": time.strftime("%H:%M:%S"),
            "level": level,
            "source": source,
            "message": message,
            "detail": detail or {},
        }
        log_store.append(entry)
    except Exception:
        pass


# ── Pipeline step helpers ─────────────────────────────────────────────────────

def step_started(step_name: str) -> None:
    try:
        pipeline_state["steps"][step_name]["status"] = "running"
        pipeline_state["steps"][step_name]["started_at"] = time.time()
    except Exception:
        pass


def step_completed(step_name: str, result_summary: str | None = None) -> None:
    try:
        step = pipeline_state["steps"][step_name]
        now = time.time()
        step["status"] = "done"
        step["completed_at"] = now
        started = step.get("started_at")
        duration = int((now - started) * 1000) if started else 0
        step["duration_ms"] = duration
        step["result_summary"] = result_summary
        emit_log("INFO", step_name, f"{step_name} completed",
                 {"duration_ms": duration, "result": result_summary})
    except Exception:
        pass


def step_failed(step_name: str, error_type: str | None = None, error_message: str | None = None) -> None:
    try:
        step = pipeline_state["steps"][step_name]
        now = time.time()
        step["status"] = "error"
        step["completed_at"] = now
        started = step.get("started_at")
        if started:
            step["duration_ms"] = int((now - started) * 1000)
        step["error"] = error_message
        emit_log("ERROR", step_name, f"{step_name} raised exception",
                 {"error_type": error_type, "error_message": error_message})
    except Exception:
        pass


# ── Pipeline lifecycle ────────────────────────────────────────────────────────

def reset_pipeline(startup_name: str) -> None:
    new = _blank_pipeline()
    new["active"] = True
    new["startup_name"] = startup_name
    new["started_at"] = time.strftime("%H:%M:%S")
    pipeline_state.clear()
    pipeline_state.update(new)


def finalize_pipeline(final_result: dict | None = None) -> None:
    pipeline_state["active"] = False
    pipeline_state["completed_at"] = time.strftime("%H:%M:%S")
    if final_result is not None:
        pipeline_state["final_result"] = final_result


def add_ollama_call(agent: str, model: str, system_prompt: str, user_prompt: str,
                    response: str, duration_ms: int, parse_success: bool) -> None:
    try:
        pipeline_state["ollama_calls"].append({
            "agent": agent,
            "model": model,
            "duration_ms": duration_ms,
            "parse_success": parse_success,
            "response_preview": (response or "")[:200],  # Debug.jsx reads this key
        })
    except Exception:
        pass
