from fastapi import APIRouter, HTTPException

from backend.schemas.chat import ChatRequest, ChatResponse, HealthResponse

router = APIRouter()


def get_agent():
    from backend.main import _agent

    return _agent


@router.get("/health", response_model=HealthResponse)
async def health_check():
    agent = get_agent()
    status = "healthy" if agent else "unhealthy"
    return HealthResponse(status=status, agent="loaded" if agent else "not loaded")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    agent = get_agent()
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        result = agent.run(request.query, session_id=request.session_id, org_id=None)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
