from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kairox_api.features.auth.services.session_service import SessionService


class FakeSessionRepo:
    def __init__(self) -> None:
        self.created = None
        self.revoked_id = None
        self.revoked_hash = None
        self.record = None

    async def create(self, user_id, raw_token, expires_at, ip_address=None, user_agent=None):
        self.created = (user_id, raw_token, expires_at, ip_address, user_agent)
        self.record = type(
            "UserSession",
            (),
            {"id": uuid4(), "user_id": user_id, "expires_at": expires_at},
        )()
        return self.record

    async def get_by_token_hash(self, token_hash):
        return self.record

    async def revoke(self, session_id):
        self.revoked_id = session_id

    async def revoke_by_token_hash(self, token_hash):
        self.revoked_hash = token_hash


@pytest.mark.asyncio
async def test_session_service_create_returns_token_and_ttl() -> None:
    repo = FakeSessionRepo()
    service = SessionService(repo)  # type: ignore[arg-type]
    user_id = uuid4()
    token, ttl = await service.create_session(user_id, False, "127.0.0.1", "agent")
    assert token
    assert ttl == 86400
    assert repo.created[0] == user_id


@pytest.mark.asyncio
async def test_session_service_validate_active_session() -> None:
    repo = FakeSessionRepo()
    user_id = uuid4()
    repo.record = type(
        "UserSession",
        (),
        {
            "id": uuid4(),
            "user_id": user_id,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        },
    )()
    service = SessionService(repo)  # type: ignore[arg-type]
    assert await service.validate("raw-token") == user_id


@pytest.mark.asyncio
async def test_session_service_revoke_delegates_to_repo() -> None:
    repo = FakeSessionRepo()
    service = SessionService(repo)  # type: ignore[arg-type]
    await service.revoke("raw-token")
    assert repo.revoked_hash is not None
