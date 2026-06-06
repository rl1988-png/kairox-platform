from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.config.trial_rules import TRIAL_DURATION_HOURS
from kairox_api.constants.enums import UserRole
from kairox_api.models.user import User
from kairox_api.models.wallet_ledger import WalletLedger


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def search(
        self, search: str = "", page: int = 1, limit: int = 20
    ) -> tuple[list[User], int]:
        query = select(User)
        count_query = select(func.count()).select_from(User)
        if search.strip():
            pattern = f"%{search.strip()}%"
            filt = or_(User.username.ilike(pattern), User.email.ilike(pattern))
            query = query.where(filt)
            count_query = count_query.where(filt)
        total = int((await self._session.execute(count_query)).scalar_one())
        offset = (page - 1) * limit
        result = await self._session.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())

    async def count_active_today(self) -> int:
        from datetime import UTC, datetime

        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self._session.execute(
            select(func.count(func.distinct(WalletLedger.user_id))).where(
                WalletLedger.created_at >= start_of_day
            )
        )
        return int(result.scalar_one())

    async def get_by_invite_code(self, invite_code: str) -> User | None:
        result = await self._session.execute(select(User).where(User.invite_code == invite_code))
        return result.scalar_one_or_none()

    async def create(
        self,
        username: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
        team_id: UUID | None = None,
        deposit_address: str | None = None,
        referrer_id: UUID | None = None,
        invite_code: str | None = None,
        trial_expires_at: datetime | None = None,
    ) -> User:
        if trial_expires_at is None and role == UserRole.USER:
            trial_expires_at = datetime.now(UTC) + timedelta(hours=TRIAL_DURATION_HOURS)

        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            team_id=team_id,
            deposit_address=deposit_address,
            referrer_id=referrer_id,
            invite_code=invite_code,
            trial_expires_at=trial_expires_at,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def count_referrals(self, user_id: UUID, level: int = 1) -> int:
        if level == 1:
            result = await self._session.execute(
                select(func.count()).select_from(User).where(User.referrer_id == user_id)
            )
            return int(result.scalar_one())
        # Level 2/3: walk referral tree (max depth 3 for MVP)
        level1 = await self._list_direct_referrals(user_id)
        if level == 2:
            if not level1:
                return 0
            result = await self._session.execute(
                select(func.count()).select_from(User).where(User.referrer_id.in_(level1))
            )
            return int(result.scalar_one())
        level2_ids = []
        for uid in level1:
            level2_ids.extend(await self._list_direct_referrals(uid))
        if not level2_ids:
            return 0
        result = await self._session.execute(
            select(func.count()).select_from(User).where(User.referrer_id.in_(level2_ids))
        )
        return int(result.scalar_one())

    async def count_valid_referrals(self, user_id: UUID, level: int = 1) -> int:
        members = await self.list_referrals_by_level(user_id, level, limit=500)
        return sum(1 for m in members if m.is_official)

    async def list_referrals_by_level(
        self, user_id: UUID, level: int, page: int = 1, limit: int = 20
    ) -> tuple[list[User], int]:
        if level == 1:
            base_ids = [user_id]
        elif level == 2:
            base_ids = await self._list_direct_referrals(user_id)
        else:
            base_ids = []
            for uid in await self._list_direct_referrals(user_id):
                base_ids.extend(await self._list_direct_referrals(uid))

        if not base_ids:
            return [], 0

        query = select(User).where(User.referrer_id.in_(base_ids))
        count_q = select(func.count()).select_from(User).where(User.referrer_id.in_(base_ids))
        total = int((await self._session.execute(count_q)).scalar_one())
        offset = (page - 1) * limit
        result = await self._session.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_unfinished_referrals(
        self, user_id: UUID, level: int, page: int = 1, limit: int = 20
    ) -> tuple[list[User], int]:
        members, total = await self.list_referrals_by_level(user_id, level, page, limit)
        unfinished = [m for m in members if not m.is_official]
        return unfinished, len(unfinished)

    async def _list_direct_referrals(self, user_id: UUID) -> list[UUID]:
        result = await self._session.execute(select(User.id).where(User.referrer_id == user_id))
        return list(result.scalars().all())

    async def get_referrer_chain(self, user_id: UUID, max_depth: int = 3) -> list[UUID]:
        chain: list[UUID] = []
        current = await self.get_by_id(user_id)
        while current is not None and current.referrer_id is not None and len(chain) < max_depth:
            chain.append(current.referrer_id)
            current = await self.get_by_id(current.referrer_id)
        return chain
