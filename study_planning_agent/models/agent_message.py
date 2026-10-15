from typing import Any

from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    sender: str = Field(min_length=1)
    receiver: str = Field(min_length=1)
    intent: str = Field(min_length=1)
    content: dict[str, Any]
    constraints: dict[str, Any] = Field(default_factory=dict)