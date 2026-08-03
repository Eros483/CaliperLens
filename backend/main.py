from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import router as v1_router
from backend.src.agent import SQLAgentGenerator
from backend.utils.logger import get_logger

logger = get_logger(__name__)
_agent: SQLAgentGenerator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    try:
        logger.info("Initializing SQL Agent...")
        _agent = SQLAgentGenerator()
        logger.info("SQL Agent ready.")
    except Exception as e:
        logger.error(f"Failed to initialize Agent: {e}")
        raise e
    yield


app = FastAPI(
    title="CaliperLens API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
