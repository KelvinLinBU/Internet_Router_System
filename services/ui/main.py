from fastapi import FastAPI
from .models import UiAck

app = FastAPI(title="ui")

@app.get("/v1/health")
def health():
    return {"status":"ok","service":"ui"}

@app.post("/v1/refresh")
def refresh():
    # stub UI action
    return UiAck().model_dump()
