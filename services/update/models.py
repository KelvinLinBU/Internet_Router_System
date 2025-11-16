from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class UpdateStatus(BaseModel):
    available_version: Optional[int] = None
    applied_version: Optional[int] = None
    last_check: Optional[datetime] = None
    last_result: Optional[str] = None
