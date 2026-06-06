import pytest
from httpx import ASGITransport, AsyncClient
from starlette.requests import Request
from starlette.responses import Response

from kairox_api.constants.enums import ErrorCode
from kairox_api.constants.limits import INVALID_CREDENTIALS_MESSAGE
from kairox_api.core.cookies import validate_csrf
from kairox_api.core.errors import AppError
from kairox_api.features.auth.services.session_service import SessionService
from kairox_api.main import app


class FakeRequest:
    method = "POST"
    cookies: dict[str, str] = {}
    headers: dict[str, str] = {}


@pytest.mark.asyncio
async def test_csrf_reject_on_logout_without_token() -> None:
    request = FakeRequest()
    with pytest.raises(AppError) as exc:
        validate_csrf(request)  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.FORBIDDEN


@pytest.mark.asyncio
async def test_logout_endpoint_requires_csrf() -> None:
    from unittest.mock import AsyncMock, patch

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.expire = AsyncMock()

    transport = ASGITransport(app=app)
    with patch("kairox_api.core.middleware.get_redis", return_value=mock_redis):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_invalid_credentials_message() -> None:
    from kairox_api.features.auth.services.auth_service import AuthService

    class EmptyUsers:
        async def get_by_username(self, username):
            return None

    class EmptyTeams:
        pass

    class FakeSessions:
        async def create_session(self, *args, **kwargs):
            return "t", 3600

        async def validate(self, token):
            return None

        async def revoke(self, token):
            pass

    service = AuthService(EmptyUsers(), EmptyTeams(), FakeSessions())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.login("unknown", "wrongpass123", False, "127.0.0.1", "test")
    assert exc.value.message == INVALID_CREDENTIALS_MESSAGE


@pytest.mark.asyncio
async def test_session_expiry_returns_none() -> None:
    from datetime import UTC, datetime, timedelta
    from uuid import uuid4

    from kairox_api.models.user import UserSession

    class ExpiredRepo:
        async def get_by_token_hash(self, token_hash):
            return UserSession(
                user_id=uuid4(),
                refresh_token_hash=token_hash,
                expires_at=datetime.now(UTC) - timedelta(hours=1),
            )

        async def revoke(self, session_id):
            pass

        async def create(self, *args, **kwargs):
            raise NotImplementedError

        async def revoke_by_token_hash(self, token_hash):
            pass

    service = SessionService(ExpiredRepo())  # type: ignore[arg-type]
    result = await service.validate("some-token")
    assert result is None


@pytest.mark.asyncio
async def test_login_rate_limit_enforced() -> None:
    from unittest.mock import AsyncMock, patch

    from kairox_api.core.auth_rate_limit import enforce_login_rate_limit

    mock_redis = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=6)
    mock_redis.expire = AsyncMock()

    with (
        patch("kairox_api.core.auth_rate_limit.get_redis", return_value=mock_redis),
        pytest.raises(AppError) as exc,
    ):
        await enforce_login_rate_limit("203.0.113.1")
    assert exc.value.code == ErrorCode.RATE_LIMITED


@pytest.mark.asyncio
async def test_login_rate_limit_fails_closed_when_redis_unavailable() -> None:
    from unittest.mock import patch

    from kairox_api.core.auth_rate_limit import enforce_login_rate_limit

    with (
        patch(
            "kairox_api.core.auth_rate_limit.get_redis",
            side_effect=RuntimeError("redis down"),
        ),
        pytest.raises(AppError) as exc,
    ):
        await enforce_login_rate_limit("203.0.113.2")
    assert exc.value.code == ErrorCode.RATE_LIMITED
    assert exc.value.status_code == 503


def _request(path: str, method: str = "POST") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": path,
            "headers": [],
            "client": ("203.0.113.3", 12345),
            "scheme": "http",
            "server": ("testserver", 80),
        }
    )


@pytest.mark.asyncio
async def test_global_rate_limit_fails_closed_for_money_routes_when_redis_unavailable() -> None:
    from unittest.mock import patch

    from kairox_api.core.middleware import RateLimitMiddleware

    async def call_next(_request: Request) -> Response:
        return Response("ok")

    middleware = RateLimitMiddleware(app=app)
    with patch("kairox_api.core.middleware.get_redis", side_effect=RuntimeError("redis down")):
        response = await middleware.dispatch(_request("/api/v1/trade/start"), call_next)

    assert response.status_code == 503


@pytest.mark.asyncio
async def test_global_rate_limit_keeps_health_open_when_redis_unavailable() -> None:
    from unittest.mock import patch

    from kairox_api.core.middleware import RateLimitMiddleware

    async def call_next(_request: Request) -> Response:
        return Response("ok")

    middleware = RateLimitMiddleware(app=app)
    with patch("kairox_api.core.middleware.get_redis", side_effect=RuntimeError("redis down")):
        response = await middleware.dispatch(_request("/health", "GET"), call_next)

    assert response.status_code == 200
