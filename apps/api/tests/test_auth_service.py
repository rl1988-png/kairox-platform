from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from kairox_api.constants.enums import ErrorCode, UserRole
from kairox_api.constants.limits import GENERIC_RESET_MESSAGE
from kairox_api.core.errors import AppError
from kairox_api.core.password import hash_password
from kairox_api.core.security import create_access_token
from kairox_api.features.auth.services.auth_service import AuthService
from kairox_api.features.withdraw.service import WithdrawService


class FakeSessionService:
    def __init__(self) -> None:
        self._user_id = None

    async def create_session(self, user_id, remember_me, ip_address, user_agent):
        self._user_id = user_id
        return "session-token", 86400

    async def validate(self, raw_token):
        return self._user_id

    async def revoke(self, raw_token):
        return None


class FakeUserRepo:
    def __init__(self) -> None:
        self.users: dict[str, object] = {}

    async def get_by_username(self, username):
        return self.users.get(username)

    async def get_by_email(self, email):
        for u in self.users.values():
            if getattr(u, "email", None) == email:
                return u
        return None

    async def get_by_id(self, user_id):
        for u in self.users.values():
            if u.id == user_id:
                return u
        return None

    async def get_by_invite_code(self, invite_code):
        return None

    async def create(
        self,
        username,
        email,
        password_hash,
        role=UserRole.USER,
        team_id=None,
        deposit_address=None,
        referrer_id=None,
        invite_code=None,
    ):
        user = type(
            "User",
            (),
            {
                "id": uuid4(),
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "team_id": team_id,
                "invite_code": invite_code,
                "referrer_id": referrer_id,
                "vip_level": 1,
                "is_official": False,
                "is_active": True,
                "created_at": datetime.now(UTC),
            },
        )()
        self.users[username] = user
        return user


class FakeTeamRepo:
    async def get_by_invite_code(self, code):
        if code == "valid-code":
            return type("Team", (), {"id": uuid4()})()
        return None


def _auth_service(user_repo=None) -> AuthService:
    return AuthService(
        user_repo or FakeUserRepo(),
        FakeTeamRepo(),
        FakeSessionService(),  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_register_creates_user() -> None:
    service = _auth_service()
    result = await service.register(
        "testuser", "test@example.com", "password123", "valid-code", "127.0.0.1", "agent"
    )
    assert result.response.user.username == "testuser"


@pytest.mark.asyncio
async def test_register_duplicate_username() -> None:
    user_repo = FakeUserRepo()
    service = _auth_service(user_repo)
    await service.register("testuser", "a@example.com", "password123", "valid-code", None, None)
    with pytest.raises(AppError) as exc:
        await service.register("testuser", "b@example.com", "password123", "valid-code", None, None)
    assert exc.value.code == ErrorCode.CONFLICT


@pytest.mark.asyncio
async def test_register_invalid_invite() -> None:
    service = _auth_service()
    with pytest.raises(AppError) as exc:
        await service.register("u", "u@example.com", "password123", "bad", None, None)
    assert exc.value.code == ErrorCode.CONFLICT


@pytest.mark.asyncio
async def test_login_success() -> None:
    user_repo = FakeUserRepo()
    password = "KairoxTest2026"
    user = await user_repo.create("lewe", "lewe@kairox.local", hash_password(password))
    service = _auth_service(user_repo)
    result = await service.login("lewe", password, False, "127.0.0.1", "agent")
    assert result.response.user.id == user.id
    assert result.response.access_token


@pytest.mark.asyncio
async def test_login_invalid_credentials() -> None:
    service = _auth_service()
    with pytest.raises(AppError) as exc:
        await service.login("nobody", "wrong", False, None, None)
    assert exc.value.code == ErrorCode.UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_inactive_user() -> None:
    user_repo = FakeUserRepo()
    password = "KairoxTest2026"
    user = await user_repo.create("inactive", "inactive@kairox.local", hash_password(password))
    user.is_active = False
    service = _auth_service(user_repo)
    with pytest.raises(AppError) as exc:
        await service.login("inactive", password, False, None, None)
    assert exc.value.code == ErrorCode.UNAUTHORIZED


@pytest.mark.asyncio
async def test_logout_revokes_session() -> None:
    revoked: list[str] = []

    class TrackingSessions(FakeSessionService):
        async def revoke(self, raw_token):
            revoked.append(raw_token)

    service = AuthService(FakeUserRepo(), FakeTeamRepo(), TrackingSessions())  # type: ignore[arg-type]
    await service.logout("session-token")
    assert revoked == ["session-token"]


@pytest.mark.asyncio
async def test_get_user_not_found() -> None:
    service = _auth_service()
    with pytest.raises(AppError) as exc:
        await service.get_user(uuid4())
    assert exc.value.code == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_authenticate_via_session_cookie() -> None:
    user_repo = FakeUserRepo()
    user = await user_repo.create("auth", "auth@kairox.local", hash_password("password123"))
    sessions = FakeSessionService()
    sessions._user_id = user.id
    service = AuthService(user_repo, FakeTeamRepo(), sessions)  # type: ignore[arg-type]
    authenticated = await service.authenticate(None, "session-token")
    assert authenticated.id == user.id


@pytest.mark.asyncio
async def test_authenticate_via_bearer_token() -> None:
    user_repo = FakeUserRepo()
    user = await user_repo.create("bearer", "bearer@kairox.local", hash_password("password123"))
    token, _ = create_access_token(str(user.id), extra={"role": user.role.value})
    service = _auth_service(user_repo)
    authenticated = await service.authenticate(f"Bearer {token}", None)
    assert authenticated.id == user.id


@pytest.mark.asyncio
async def test_authenticate_missing_credentials() -> None:
    service = _auth_service()
    with pytest.raises(AppError) as exc:
        await service.authenticate(None, None)
    assert exc.value.code == ErrorCode.UNAUTHORIZED


@pytest.mark.asyncio
async def test_build_me_response_returns_fresh_tokens() -> None:
    user_repo = FakeUserRepo()
    user = await user_repo.create("me", "me@kairox.local", hash_password("password123"))
    service = _auth_service(user_repo)
    # build_me_response no longer touches the session — it returns only fresh tokens.
    auth_response = await service.build_me_response(user)
    assert auth_response.access_token
    assert auth_response.csrf_token
    assert auth_response.user.username == "me"


@pytest.mark.asyncio
async def test_request_password_reset_generic_message() -> None:
    from unittest.mock import AsyncMock, patch

    user_repo = FakeUserRepo()
    await user_repo.create("reset", "reset@kairox.local", hash_password("password123"))
    mock_redis = AsyncMock()
    service = _auth_service(user_repo)
    with patch("kairox_api.features.auth.services.auth_service.get_redis", return_value=mock_redis):
        message = await service.request_password_reset("reset@kairox.local")
    assert message == GENERIC_RESET_MESSAGE
    mock_redis.setex.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_token() -> None:
    from unittest.mock import AsyncMock, patch

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    service = _auth_service()
    with (
        patch("kairox_api.features.auth.services.auth_service.get_redis", return_value=mock_redis),
        pytest.raises(AppError) as exc,
    ):
        await service.confirm_password_reset("bad-token", "newpassword123")
    assert exc.value.code == ErrorCode.NOT_FOUND


class FakeWithdrawRepo:
    async def create(self, user_id, amount, fee_amount, to_address):
        return type("Withdrawal", (), {"id": uuid4(), "amount": amount})()

    async def list_for_user(self, user_id):
        return []

    async def list_pending(self):
        return []

    async def get_by_id(self, request_id):
        return None

    async def get_pending_for_user(self, user_id):
        return None


class FakeLedgerRepo:
    def __init__(self) -> None:
        self.available = Decimal("500")
        self.locked = Decimal("0")

    async def get_balance(self, user_id):
        return type("Bal", (), {"available": self.available, "locked": self.locked})()

    async def lock(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        from kairox_api.repositories.exceptions import InsufficientBalanceError

        if self.available < amount:
            raise InsufficientBalanceError()
        self.available -= amount
        self.locked += amount


def _withdraw_user(**kwargs: object) -> object:
    defaults = {
        "id": uuid4(),
        "is_official": True,
        "withdrawal_address": "T" + "a" * 33,
    }
    defaults.update(kwargs)
    return type("User", (), defaults)()


@pytest.mark.asyncio
async def test_withdraw_request_locks_funds() -> None:
    ledger = FakeLedgerRepo()
    service = WithdrawService(FakeWithdrawRepo(), ledger)  # type: ignore[arg-type]
    await service.create_request(_withdraw_user(), Decimal("50"))  # type: ignore[arg-type]
    assert ledger.available == Decimal("449")


@pytest.mark.asyncio
async def test_withdraw_min_amount_validation() -> None:
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.create_request(_withdraw_user(), Decimal("5"))  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_withdraw_invalid_address() -> None:
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    user = _withdraw_user(withdrawal_address=None)
    with pytest.raises(AppError) as exc:
        await service.bind_address(user, "TRC20", "short")  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.VALIDATION_ERROR
