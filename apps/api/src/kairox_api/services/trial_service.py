from datetime import UTC, datetime

from kairox_api.models.user import User


class TrialService:
    """Trial window enforcement for non-official accounts."""

    @staticmethod
    def is_trial_active(user: User, now: datetime | None = None) -> bool:
        if user.is_official:
            return True
        if user.trial_expires_at is None:
            return True
        current = now or datetime.now(UTC)
        return current <= user.trial_expires_at

    @staticmethod
    def assert_trial_active(user: User, now: datetime | None = None) -> None:
        from kairox_api.constants.enums import ErrorCode
        from kairox_api.core.errors import AppError

        if TrialService.is_trial_active(user, now):
            return
        raise AppError(
            ErrorCode.FORBIDDEN,
            "Trial period expired — recharge to continue trading",
            403,
        )
