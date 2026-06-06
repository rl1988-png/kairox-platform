from dataclasses import dataclass
from decimal import Decimal

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from kairox_api.constants.enums import ErrorCode, UserRole
from kairox_api.core.cookies import get_session_token
from kairox_api.core.database import get_db_session
from kairox_api.core.errors import AppError
from kairox_api.features.auth.services.auth_service import AuthService
from kairox_api.features.auth.services.session_service import SessionService
from kairox_api.features.recharge.service import RechargeService
from kairox_api.features.recharge.services.tron_client import TronClient
from kairox_api.features.support.service import SupportService
from kairox_api.features.trade.service import TradeService
from kairox_api.models.user import User
from kairox_api.repositories.audit_repository import AuditRepository
from kairox_api.repositories.ledger_repository import LedgerRepository
from kairox_api.repositories.order_repository import RechargeRepository, TradeRepository
from kairox_api.repositories.session_repository import SessionRepository
from kairox_api.repositories.team_earning_repository import TeamEarningRepository
from kairox_api.repositories.team_repository import TeamRepository
from kairox_api.repositories.user_repository import UserRepository
from kairox_api.repositories.withdraw_repository import WithdrawRepository
from kairox_api.services.admin_service import AdminService
from kairox_api.services.ai_analysis_service import AiAnalysisService
from kairox_api.services.registration_bonus_service import RegistrationBonusService
from kairox_api.services.support_verify_service import SupportVerifyService
from kairox_api.services.team_commission_service import TeamCommissionService
from kairox_api.services.team_service import TeamService
from kairox_api.services.user_activation_service import UserActivationService
from kairox_api.services.withdraw_service import WithdrawService


@dataclass
class ServiceContainer:
    auth: AuthService
    trade: TradeService
    recharge: RechargeService
    withdraw: WithdrawService
    support: SupportService
    admin: AdminService
    ai: AiAnalysisService
    team: TeamService
    support_verify: SupportVerifyService
    ledger_repo: LedgerRepository
    team_repo: TeamRepository
    audit_repo: AuditRepository


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def build_container(session: AsyncSession) -> ServiceContainer:
    user_repo = UserRepository(session)
    ledger_repo = LedgerRepository(session)
    team_repo = TeamRepository(session)
    trade_repo = TradeRepository(session)
    recharge_repo = RechargeRepository(session)
    withdraw_repo = WithdrawRepository(session)
    session_repo = SessionRepository(session)
    audit_repo = AuditRepository(session)
    tron_client = TronClient()
    session_service = SessionService(session_repo)
    withdraw_service = WithdrawService(withdraw_repo, ledger_repo)
    team_earning_repo = TeamEarningRepository(session)
    activation_service = UserActivationService(user_repo, ledger_repo)
    team_commission_service = TeamCommissionService(user_repo, team_earning_repo, ledger_repo)
    registration_bonus_service = RegistrationBonusService(ledger_repo)

    return ServiceContainer(
        auth=AuthService(user_repo, team_repo, session_service, registration_bonus_service),
        trade=TradeService(trade_repo, ledger_repo, user_repo, team_commission_service),
        recharge=RechargeService(recharge_repo, ledger_repo, tron_client, activation_service),
        withdraw=withdraw_service,
        support=SupportService(recharge_repo, tron_client),
        admin=AdminService(
            user_repo,
            ledger_repo,
            audit_repo,
            recharge_repo,
            trade_repo,
            withdraw_repo,
            withdraw_service,
        ),
        support_verify=SupportVerifyService(recharge_repo, tron_client),
        ai=AiAnalysisService(),
        team=TeamService(team_repo, user_repo, session),
        ledger_repo=ledger_repo,
        team_repo=team_repo,
        audit_repo=audit_repo,
    )


async def get_container(session: AsyncSession = Depends(get_db_session)) -> ServiceContainer:
    return build_container(session)


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    container: ServiceContainer = Depends(get_container),
) -> User:
    return await container.auth.authenticate(authorization, get_session_token(request))


async def get_session_user(
    request: Request,
    container: ServiceContainer = Depends(get_container),
) -> User:
    """Authenticate via session cookie only — rejects bare bearer tokens.

    Used by /me to prevent infinite token refresh: a logged-out bearer token
    must not be able to mint new tokens without an active session.
    """
    return await container.auth.authenticate(None, get_session_token(request))


def require_roles(*roles: UserRole):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise AppError(ErrorCode.FORBIDDEN, "Insufficient permissions", 403)
        return user

    return checker


def decimal_str(value: Decimal | float | int) -> str:
    return format(Decimal(str(value)).normalize(), "f")
