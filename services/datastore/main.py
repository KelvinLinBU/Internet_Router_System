from fastapi import FastAPI, HTTPException
from typing import Dict, List
from .models import VersionedConfig, BlockEntry

app = FastAPI(title="datastore")

_store: Dict[str, object] = {
    "config": VersionedConfig(version=1, payload={}),
    "blocklist": []  # List[BlockEntry]
}

@app.get("/v1/health")
def health():
    return {"status":"ok","service":"datastore"}

@app.get("/v1/config", response_model=VersionedConfig)
def get_config():
    return _store["config"]  # type: ignore

@app.post("/v1/config", response_model=VersionedConfig)
def set_config(cfg: VersionedConfig):
    _store["config"] = cfg
    return cfg

@app.get("/v1/blocklist", response_model=List[BlockEntry])
def get_blocklist():
    return _store["blocklist"]  # type: ignore

@app.post("/v1/blocklist", response_model=BlockEntry)
def add_block(entry: BlockEntry):
    bl: List[BlockEntry] = _store["blocklist"]  # type: ignore
    bl.append(entry)
    return entry
