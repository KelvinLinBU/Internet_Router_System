from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class Rule(BaseModel):
    id: int
    pattern: str
    enabled: bool = True

class RulesAck(BaseModel):
    accepted: bool = True
    rules_active: int
    at: datetime = Field(default_factory=datetime.utcnow)
