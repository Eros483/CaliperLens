from pydantic import BaseModel, Field

from backend.core.planner import Plan


class ChatRequest(BaseModel):
    query: str
    session_id: str = Field(default="default_session")


class ChatResponse(BaseModel):
    response: str
    success: bool = True
    plan: Plan | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class HealthResponse(BaseModel):
    status: str
    agent: str
