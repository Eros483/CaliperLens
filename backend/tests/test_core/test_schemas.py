from backend.schemas.chat import ChatRequest, ChatResponse, HealthResponse


class TestSchemas:
    def test_chat_request_defaults(self):
        req = ChatRequest(query="test query")
        assert req.query == "test query"
        assert req.session_id == "default_session"

    def test_chat_request_custom_session(self):
        req = ChatRequest(query="q", session_id="session123")
        assert req.session_id == "session123"

    def test_chat_response_default(self):
        resp = ChatResponse(response="hello")
        assert resp.response == "hello"
        assert resp.success is True

    def test_health_response_fields(self):
        h = HealthResponse(status="healthy", agent="loaded")
        assert h.status == "healthy"
        assert h.agent == "loaded"
