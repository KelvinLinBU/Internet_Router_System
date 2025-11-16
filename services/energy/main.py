# services/energy/main.py
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, Body

app = FastAPI(title="energy")

# ---- Models (inlined to avoid import issues) ----
class ModeEnum(str, Enum):
    active = "active"
    low = "low"          # alias for standby/low-power
    standby = "standby"  # alias accepted

class PowerState:
    def __init__(self) -> None:
        self.mode: ModeEnum = ModeEnum.active
        self.power_watts: float = 6.0
        self.version_seen: Optional[int] = None
        self.last_change: datetime = datetime.utcnow()

    def set_mode(self, mode: ModeEnum) -> None:
        self.mode = mode
        # simple demo power model
        self.power_watts = 6.0 if mode == ModeEnum.active else 1.5
        self.last_change = datetime.utcnow()

_state = PowerState()

# ---- Helpers ----
def normalize_mode(value: Optional[str]) -> Optional[ModeEnum]:
    if not value:
        return None
    v = value.strip().lower()
    if v in ("active",):
        return ModeEnum.active
    if v in ("low", "low-power", "standby", "sleep"):
        return ModeEnum.low
    return None

def ok(payload: Dict[str, Any] = {}) -> Dict[str, Any]:
    return {"ok": True, **payload}

# ---- Endpoints ----
@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "energy"}

@app.post("/v1/notify/config")
def notify(body: Dict[str, Any] = Body(default={})):
    # Orchestration will POST {"version": int, ...}
    _state.version_seen = body.get("version")
    return ok({"version": _state.version_seen})

# Accept multiple paths/payload shapes for mode changes to keep scripts simple
@app.post("/v1/mode")
@app.post("/v1/energy/mode")
@app.post("/v1/power/mode")
def set_mode(
    body: Dict[str, Any] = Body(default={}),
    mode_q: Optional[str] = None,  # allow ?mode=active
    state_q: Optional[str] = None  # allow ?state=active
):
    # Accept {"mode":"active"} or {"state":"active"} or query params
    mode = normalize_mode(
        (body.get("mode") or body.get("state") or mode_q or state_q)
    )
    if mode is None:
        return {"ok": False, "detail": "mode must be one of: active, low (standby)"}
    _state.set_mode(mode)
    return ok({"mode": _state.mode, "power_watts": _state.power_watts, "changed_at": _state.last_change.isoformat()})

@app.get("/v1/power")
def power():
    return {
        "mode": _state.mode,
        "power_watts": _state.power_watts,
        "last_change": _state.last_change.isoformat(),
        "config_version_seen": _state.version_seen,
    }

# Lightweight KPI so orchestration can aggregate power usage
@app.get("/v1/kpi")
def kpi():
    return {
        "power_watts": _state.power_watts,
        "mode": _state.mode,
        # placeholders for a consistent KPI schema across services
        "throughput_mbps": None,
        "p95_latency_ms": None,
        "active_clients": None,
        "firewall_rules_active": None,
    }
