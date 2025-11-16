from pydantic import BaseModel, Field
from datetime import datetime

class PowerState(BaseModel):
    mode: str = "active"      # "active" or "standby"
    power_watts: float = 6.0  # demo defaults
    at: datetime = Field(default_factory=datetime.utcnow)
