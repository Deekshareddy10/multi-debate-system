from pydantic import BaseModel
from typing import Optional

class DebateRequest(BaseModel):
    topic: str
    context: Optional[str] = None #default is none