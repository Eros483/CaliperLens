from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for incoming chat messages."""

    query: str
    session_id: str = Field(default="default_session")


class ChatResponse(BaseModel):
    """Schema for the AI response."""

    response: str
    success: bool = True


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str
    agent: str
