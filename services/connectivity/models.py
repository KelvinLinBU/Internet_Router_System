from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Client(BaseModel):
    id: str
    type: str  # "wifi" or "ethernet"
    rssi_dbm: Optional[int] = None

class KPI(BaseModel):
    throughput_mbps: float = 300.0
    p95_latency_ms: float = 40.0
    active_clients: int = 0
    at: datetime = Field(default_factory=datetime.utcnow)
