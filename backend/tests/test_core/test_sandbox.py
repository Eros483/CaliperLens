from unittest.mock import MagicMock, patch

import pytest

from backend.core.sandbox import SandboxError, SandboxExecutor, SandboxTimeout

DUMMY_IMAGE = "caliperlens-sandbox"


class TestSandboxExecutor:
    def test_execute_returns_result_on_success(self):
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.side_effect = [b"hello world\n", b""]
        mock_client.containers.run.return_value = mock_container

        executor = SandboxExecutor.__new__(SandboxExecutor)
        executor.image_name = DUMMY_IMAGE
        executor.db_path = "/tmp/nonexistent.duckdb"
        executor._docker = mock_client
        executor._image_built = True

        result = executor.execute("print('hello world')", timeout=10)
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]

    def test_execute_captures_exit_code(self):
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 1}
        mock_container.logs.side_effect = [b"", b"error: something broke\n"]
        mock_client.containers.run.return_value = mock_container

        executor = SandboxExecutor.__new__(SandboxExecutor)
        executor.image_name = DUMMY_IMAGE
        executor.db_path = "/tmp/nonexistent.duckdb"
        executor._docker = mock_client
        executor._image_built = True

        result = executor.execute("raise Exception('fail')", timeout=10)
        assert result["exit_code"] == 1

    def test_timeout_raises_sandbox_timeout(self):
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.wait.side_effect = Exception("timeout")
        mock_client.containers.run.return_value = mock_container

        executor = SandboxExecutor.__new__(SandboxExecutor)
        executor.image_name = DUMMY_IMAGE
        executor.db_path = "/tmp/nonexistent.duckdb"
        executor._docker = mock_client
        executor._image_built = True

        with pytest.raises(SandboxTimeout):
            executor.execute("while True: pass", timeout=1)

    def test_no_docker_raises_sandbox_error(self):
        with patch("backend.core.sandbox.docker") as mock_docker:
            mock_docker.from_env.side_effect = Exception("docker not running")
            executor = SandboxExecutor()

            with pytest.raises(SandboxError, match="Docker not available"):
                _ = executor.docker_client

    def test_health_check_returns_true_for_ok(self):
        mock_client = MagicMock()
        executor = SandboxExecutor.__new__(SandboxExecutor)
        executor.image_name = DUMMY_IMAGE
        executor.db_path = "/tmp/nonexistent.duckdb"
        executor._docker = mock_client
        executor._image_built = True
        executor.execute = MagicMock(return_value={"exit_code": 0, "stdout": "sandbox_ok"})

        assert executor.health_check() is True
