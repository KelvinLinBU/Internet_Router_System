from fastapi import FastAPI
import os, httpx, asyncio
from .models import ApplyConfigRequest, NotifyRequest, Ack, OrchestrationStatus, KPI

app = FastAPI(title="orchestration")

# Service URLs (docker-compose service names)
DS  = os.getenv("DATASTORE_URL",   "http://ds:8000")
SEC = os.getenv("SECURITY_URL",    "http://security:8000")
CON = os.getenv("CONNECTIVITY_URL","http://connectivity:8000")
UPD = os.getenv("UPDATE_URL",      "http://update:8000")
ENG = os.getenv("ENERGY_URL",      "http://energy:8000")

_state = OrchestrationStatus(version=1)

@app.get("/v1/health")
def health():
    return {"status":"ok","service":"orchestration"}

@app.get("/v1/status", response_model=OrchestrationStatus)
def status():
    return _state

@app.post("/v1/config/apply", response_model=Ack)
async def apply_config(body: ApplyConfigRequest):
    """
    1) Store the version+payload in Data Store (opaque)
    2) Notify functions to load version
    3) Return Ack with any errors aggregated
    """
    errors = []
    # 1) write to Data Store
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(f"{DS}/v1/config", json={"version": body.version, "payload": body.payload})
            r.raise_for_status()
    except Exception as e:
        errors.append(f"datastore: {type(e).__name__}: {e}")

    # 2) notify services
    targets = [SEC, CON, UPD, ENG]
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            for base in targets:
                try:
                    await client.post(f"{base}/v1/notify/config", json={"version": body.version, "targets": []})
                except Exception as e:
                    errors.append(f"{base}: {type(e).__name__}: {e}")
    except Exception as e:
        errors.append(f"notify-loop: {type(e).__name__}: {e}")

    # update local status
    _state.version = body.version
    return Ack(ok=(len(errors)==0), version=body.version, detail="; ".join(errors) if errors else None)

@app.get("/v1/kpi", response_model=KPI)
async def kpi():
    """
    Pull KPIs from services (best effort) and return a merged view.
    """
    out = KPI()
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            r = await client.get(f"{CON}/v1/kpi")
            c = r.json()
            out.throughput_mbps = c.get("throughput_mbps")
            out.p95_latency_ms = c.get("p95_latency_ms")
            out.active_clients = c.get("active_clients")
        except Exception:
            pass
        try:
            r = await client.get(f"{ENG}/v1/power")
            out.power_watts = r.json().get("power_watts")
        except Exception:
            pass
        try:
            r = await client.get(f"{SEC}/v1/rules/count")
            out.firewall_rules_active = r.json().get("rules_active")
        except Exception:
            pass
    _state.kpi = out
    return out
