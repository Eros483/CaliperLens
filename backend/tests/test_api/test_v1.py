import pytest

HAVE_DEPS = True
try:
    from fastapi.testclient import TestClient

    from backend.main import app
except ImportError:
    HAVE_DEPS = False


@pytest.mark.skipif(not HAVE_DEPS, reason="Backend dependencies not installed")
class TestHealthEndpoint:
    def test_health_returns_unhealthy_when_agent_not_loaded(self):
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"


@pytest.mark.skipif(not HAVE_DEPS, reason="Backend dependencies not installed")
class TestChatEndpoint:
    def test_chat_without_agent_returns_503(self):
        client = TestClient(app)
        response = client.post(
            "/api/v1/chat",
            json={"query": "test", "session_id": "test"},
        )
        assert response.status_code == 503
