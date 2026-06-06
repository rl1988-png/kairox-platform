import os
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import kairox_api.models  # noqa: F401
from kairox_api.constants.enums import LedgerEntryType, UserRole
from kairox_api.core.database import Base
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.user_repository import UserRepository

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://kairox:kairox_dev_password@localhost:5432/kairox_test",
)


@pytest.fixture
async def db_session() -> AsyncSession:
    try:
        engine = create_async_engine(TEST_DATABASE_URL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            yield session
        await engine.dispose()
    except (OSError, Exception) as exc:
        pytest.skip(f"PostgreSQL not available: {exc}")


@pytest.fixture
async def ledger_user(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    user = await user_repo.create(
        username=f"ledger_{os.urandom(4).hex()}",
        email=f"{os.urandom(4).hex()}@test.local",
        password_hash="hash",
        role=UserRole.USER,
    )
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_repository_credit_persists_entry(
    db_session: AsyncSession, ledger_user: object
) -> None:
    repo = LedgerRepository(db_session)
    user_id = ledger_user.id  # type: ignore[attr-defined]
    await repo.credit(user_id, Decimal("100"), LedgerEntryType.RECHARGE)
    balance = await repo.get_balance(user_id)
    assert balance.available == Decimal("100")
    assert await repo.sum_available_deltas(user_id) == balance.available
