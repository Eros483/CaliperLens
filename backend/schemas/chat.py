from pydantic import BaseModel, Field

from backend.core.planner import Plan


class ChatRequest(BaseModel):
    query: str
    session_id: str = Field(default="default_session")


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    plan: Plan | None = None


class HealthResponse(BaseModel):
    status: str
    agent: str
