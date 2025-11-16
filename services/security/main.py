# services/security/main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Set

app = FastAPI(title="security")

# Simple in-memory store for the demo
BLOCKLIST: Set[str] = set()

class Domains(BaseModel):
    domains: List[str]

@app.get("/v1/health")
def health():
    return {"ok": True}

@app.get("/v1/kpi")
def kpi():
    return {
        "firewall_rules_active": 0,
        "blocked_domains": len(BLOCKLIST),
    }

@app.get("/v1/blocklist")
def get_blocklist():
    # Return a plain list for simplicity
    return sorted(BLOCKLIST)

# Accept BOTH styles: JSON body or single query param (?domain=)
@app.post("/v1/blocklist/add")
def add_blocklist(
    body: Optional[Domains] = None,
    domain: Optional[str] = Query(None)
):
    added = 0

    if body and body.domains:
        for d in body.domains:
            d = (d or "").strip().lower()
            if "." not in d:
                raise HTTPException(status_code=422, detail=f"invalid domain: {d}")
            if d not in BLOCKLIST:
                BLOCKLIST.add(d); added += 1

    if domain:
        d = domain.strip().lower()
        if "." not in d:
            raise HTTPException(status_code=422, detail=f"invalid domain: {d}")
        if d not in BLOCKLIST:
            BLOCKLIST.add(d); added += 1

    if added == 0 and not (body and body.domains) and not domain:
        raise HTTPException(status_code=422, detail="no domains provided")

    return {"added": added, "total": len(BLOCKLIST)}

@app.post("/v1/notify/config")
def notify_config(version: int):
    # No-op for demo; in a full system this would re-load policy
    return {"ack": True, "version": version}
