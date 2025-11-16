from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Target(str, Enum):
    CONNECTIVITY = "connectivity"
    SECURITY = "security"
    ENERGY = "energy"
    UPDATE = "update"
    UI = "ui"

class Ack(BaseModel):
    ok: bool = True
    version: Optional[int] = None
    detail: Optional[str] = None
    at: datetime = Field(default_factory=datetime.utcnow)

class ApplyConfigRequest(BaseModel):
    version: int
    payload: Dict[str, Any] = Field(default_factory=dict)  # opaque to orchestration
    note: Optional[str] = None

class NotifyRequest(BaseModel):
    version: int
    targets: List[Target] = Field(default_factory=list)

class KPI(BaseModel):
    throughput_mbps: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    power_watts: Optional[float] = None
    active_clients: Optional[int] = None
    firewall_rules_active: Optional[int] = None

class OrchestrationStatus(BaseModel):
    version: int
    kpi: KPI = KPI()
    last_update_check: Optional[datetime] = None
