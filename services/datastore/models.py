from typing import Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class VersionedConfig(BaseModel):
    version: int
    payload: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BlockEntry(BaseModel):
    domain: str
    enabled: bool = True
    added_at: datetime = Field(default_factory=datetime.utcnow)
