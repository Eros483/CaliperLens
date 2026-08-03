from backend.utils.config import Settings


class TestSettings:
    def test_database_uri_construction(self):
        s = Settings(db_user="test_user", db_password="pass", db_host="db", db_name="testdb")
        uri = s.database_uri
        assert "test_user" in uri
        assert "db" in uri
        assert "testdb" in uri

    def test_model_reads_env_file(self, monkeypatch):
        monkeypatch.setenv("DB_USER", "env_user")
        monkeypatch.setenv("DB_PASSWORD", "env_pass")
        monkeypatch.setenv("DB_HOST", "env_host")
        monkeypatch.setenv("DB_NAME", "env_db")
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        s = Settings()
        assert s.db_user == "env_user"
        assert s.db_host == "env_host"
        assert s.gemini_api_key == "test-key"

    def test_database_uri_property(self):
        s = Settings(db_user="u", db_password="p", db_host="h", db_name="n")
        uri = s.database_uri
        assert uri.startswith("mysql+pymysql://")
        assert "@h/" in uri

    def test_gemini_api_key_default(self):
        s = Settings()
        assert s.gemini_api_key == ""
