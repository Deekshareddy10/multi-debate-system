from pydantic import BaseModel
from typing import List, Optional

class DebateState(BaseModel):
    debate_id: str
    topic: str
    context: Optional[str] = None
    rounds: List = []
    status: str