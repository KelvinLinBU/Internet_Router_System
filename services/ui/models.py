from pydantic import BaseModel

class UiAck(BaseModel):
    ok: bool = True
