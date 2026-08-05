import pytest

from backend.core.auth import (
    RateLimiter,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class TestJWT:
    def test_create_and_verify_access_token(self):
        token = create_access_token("user1", org_id=16)
        payload = verify_token(token)
        assert payload.sub == "user1"
        assert payload.org_id == 16

    def test_create_and_verify_refresh_token(self):
        token = create_refresh_token("user1")
        payload = verify_token(token)
        assert payload.sub == "user1"

    def test_invalid_token_returns_401(self):
        with pytest.raises(Exception):
            verify_token("not.a.valid.token")


class TestRateLimiter:
    def test_allows_requests_within_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert limiter.is_allowed("key1") is True

    def test_blocks_requests_over_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is False

    def test_different_keys_dont_affect_each_other(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is True
        assert limiter.is_allowed("key1") is False
        assert limiter.is_allowed("key2") is True
