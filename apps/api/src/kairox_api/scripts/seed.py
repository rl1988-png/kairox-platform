"""Seed development data — admin + 2 test users + default team."""

import asyncio
from decimal import Decimal

from kairox_api.config.settings import settings
from kairox_api.constants.enums import LedgerEntryType, UserRole
from kairox_api.core.database import SessionLocal
from kairox_api.core.password import hash_password
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.team_repository import TeamRepository
from kairox_api.repositories.user_repository import UserRepository

SEED_PASSWORD = "KairoxTest2026"
DEFAULT_INVITE_CODE = "KAIROX-DEV"

SEED_USERS = (
    ("admin", "admin@kairox.local", UserRole.ADMIN, Decimal("0")),
    ("kxtest01", "kxtest01@kairox.local", UserRole.USER, Decimal("1000")),
    ("kxtest02", "kxtest02@kairox.local", UserRole.USER, Decimal("500")),
)


async def seed() -> None:
    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        ledger_repo = LedgerRepository(session)
        team_repo = TeamRepository(session)

        team = await team_repo.get_by_invite_code(DEFAULT_INVITE_CODE)
        if team is None:
            team = await team_repo.create("Kairox Dev Team", DEFAULT_INVITE_CODE)

        for username, email, role, initial_balance in SEED_USERS:
            existing = await user_repo.get_by_username(username)
            if existing is None:
                user = await user_repo.create(
                    username=username,
                    email=email,
                    password_hash=hash_password(SEED_PASSWORD),
                    role=role,
                    team_id=team.id if role == UserRole.USER else None,
                    deposit_address=settings.tron_deposit_address or None,
                )
                if initial_balance > 0:
                    await ledger_repo.credit(
                        user.id,
                        initial_balance,
                        LedgerEntryType.RECHARGE,
                        reference_type="seed",
                    )

        await session.commit()
        print(
            f"Seed completed: admin, kxtest01, kxtest02 "
            f"(password: {SEED_PASSWORD}, invite: {DEFAULT_INVITE_CODE})"
        )


if __name__ == "__main__":
    asyncio.run(seed())
