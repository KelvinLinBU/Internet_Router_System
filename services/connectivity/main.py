# services/connectivity/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import random

app = FastAPI(title="connectivity")

# -----------------------------
# In-memory demo state
# -----------------------------
_current_config_version: int = 1
_clients: List[dict] = []  # {"id": str, "medium": "wifi"|"ethernet", "rssi_dbm": int}
_last_kpi = {
    "throughput_mbps": 300.0,   # demo baseline
    "p95_latency_ms": 40.0,     # demo baseline
}

# -----------------------------
# Models
# -----------------------------
class Health(BaseModel):
    status: str = "ok"
    service: str = "connectivity"

class NotifyConfig(BaseModel):
    version: int
    targets: Optional[List[str]] = None  # accepted but unused in this demo

class Ack(BaseModel):
    ok: bool = True
    version: Optional[int] = None
    detail: Optional[str] = None
    at: datetime = Field(default_factory=datetime.utcnow)

class SimulateClientsReq(BaseModel):
    count: int = Field(ge=0, le=256, description="How many active demo clients to simulate")

class KPI(BaseModel):
    throughput_mbps: float
    p95_latency_ms: float
    active_clients: int

# -----------------------------
# Helpers
# -----------------------------
def _recompute_kpi() -> KPI:
    """
    Very simple demo model:
      - baseline throughput 300 Mbps, 40 ms p95 latency
      - each client adds a little contention; keep numbers friendly
    """
    n = len(_clients)
    # cap to avoid negative in edge cases
    throughput = max(50.0, _last_kpi["throughput_mbps"] - n * 5.0)
    latency = min(120.0, _last_kpi["p95_latency_ms"] + n * 2.0)
    return KPI(throughput_mbps=throughput, p95_latency_ms=latency, active_clients=n)

def _mk_client(i: int) -> dict:
    return {
        "id": f"client-{i+1}",
        "medium": random.choice(["wifi", "ethernet"]),
        "rssi_dbm": random.randint(-65, -40),
    }

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/v1/health", response_model=Health)
def health():
    return Health()

@app.post("/v1/notify/config", response_model=Ack)
def notify_config(nc: NotifyConfig):
    global _current_config_version
    _current_config_version = nc.version
    # In a real system, we'd reload NAT/DHCP/QoS/SSIDs here based on the Data Store.
    return Ack(ok=True, version=_current_config_version, detail="config applied")

@app.post("/v1/clients/simulate")
def simulate_clients(req: SimulateClientsReq):
    """
    Create an in-memory set of 'active clients' for demo/testing.
    """
    global _clients
    _clients = [_mk_client(i) for i in range(req.count)]
    return {"created": len(_clients)}

@app.get("/v1/clients")
def list_clients():
    """
    Optional listing used by some scripts; handy for debugging.
    """
    return _clients

@app.get("/v1/kpi", response_model=KPI)
def kpi():
    return _recompute_kpi()
