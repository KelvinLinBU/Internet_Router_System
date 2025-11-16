# services/update/main.py
from typing import Optional, Dict, Any, Union
from datetime import datetime
from fastapi import FastAPI, Body

app = FastAPI(title="update")

# ---- Inlined model/state to avoid import issues ----
VersionType = Union[int, str]

class UpdateState:
    def __init__(self) -> None:
        self.available_version: Optional[VersionType] = None
        self.applied_version: VersionType = "demo-1"   # default demo start
        self.previous_version: Optional[VersionType] = None
        self.last_check: Optional[datetime] = None
        self.last_result: Optional[str] = None         # "check_ok", "apply_ok", "apply_failed", "rollback_ok"
        self.last_action_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available_version": self.available_version,
            "applied_version": self.applied_version,
            "previous_version": self.previous_version,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_result": self.last_result,
            "last_action_at": self.last_action_at.isoformat() if self.last_action_at else None,
        }

_state = UpdateState()

# ---- helpers ----
def next_demo_version(current: VersionType) -> str:
    """
    Tiny helper to produce a plausible "next" version for the demo.
    If current is an int -> increment. If it's 'demo-X' -> bump X.
    Otherwise, append '-next'.
    """
    if isinstance(current, int):
        return str(current + 1)
    s = str(current)
    if s.startswith("demo-"):
        try:
            n = int(s.split("-", 1)[1])
            return f"demo-{n+1}"
        except Exception:
            return s + "-next"
    return s + "-next"

# ---- endpoints ----
@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "update"}

@app.post("/v1/notify/config")
def notify(body: Dict[str, Any] = Body(default={})):
    # no-op for demo; just echo version if present
    return {"ok": True, "version": body.get("version")}

@app.post("/v1/check")
def check():
    _state.last_check = datetime.utcnow()
    _state.available_version = next_demo_version(_state.applied_version)
    _state.last_result = "check_ok"
    _state.last_action_at = datetime.utcnow()
    return _state.to_dict()

@app.post("/v1/apply")
def apply(body: Dict[str, Any] = Body(default={})):
    """
    Accepts JSON like: {"version": "demo-2", "simulate_fail": false}
    On success:
      - previous_version <- applied_version
      - applied_version  <- version
    On simulate_fail:
      - do not change applied_version; set last_result="apply_failed"
    """
    target: Optional[VersionType] = body.get("version")
    simulate_fail: bool = bool(body.get("simulate_fail", False))

    if target is None:
        return {"ok": False, "detail": "Missing 'version' in request body"}

    if simulate_fail:
        _state.last_result = "apply_failed"
        _state.last_action_at = datetime.utcnow()
        return {"ok": False, "detail": "health check failed (simulated); not applied", **_state.to_dict()}

    _state.previous_version = _state.applied_version
    _state.applied_version = target
    _state.last_result = "apply_ok"
    _state.last_action_at = datetime.utcnow()
    return {"ok": True, "applied_version": _state.applied_version, **_state.to_dict()}

@app.post("/v1/rollback")
def rollback():
    """
    Roll back to previous_version if available.
    """
    if _state.previous_version is None:
        return {"ok": False, "detail": "No previous version to roll back to", **_state.to_dict()}

    _state.applied_version, _state.previous_version = _state.previous_version, _state.applied_version
    _state.last_result = "rollback_ok"
    _state.last_action_at = datetime.utcnow()
    return {"ok": True, **_state.to_dict()}

@app.get("/v1/status")
def status():
    return _state.to_dict()
