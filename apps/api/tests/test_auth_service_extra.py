from uuid import uuid4

import pytest

from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError
from kairox_api.features.auth.services.auth_service import AuthService


class FakeUserRepo:
    async def get_by_id(self, user_id):
        return None


class FakeTeamRepo:
    pass


class FakeSessionService:
    async def create_session(self, *args, **kwargs):
        return "t", 3600

    async def validate(self, token):
        return None

    async def revoke(self, token):
        pass


@pytest.mark.asyncio
async def test_get_user_not_found() -> None:
    service = AuthService(FakeUserRepo(), FakeTeamRepo(), FakeSessionService())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.get_user(uuid4())
    assert exc.value.code == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_auth_get_user_found() -> None:
    user_id = uuid4()

    class FoundUserRepo:
        async def get_by_id(self, uid):
            return type("User", (), {"id": uid})()

    service = AuthService(FoundUserRepo(), FakeTeamRepo(), FakeSessionService())  # type: ignore[arg-type]
    user = await service.get_user(user_id)
    assert user.id == user_id
