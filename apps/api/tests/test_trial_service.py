from datetime import UTC, datetime, timedelta

import pytest

from kairox_api.constants.enums import ErrorCode
from kairox_api.core.errors import AppError
from kairox_api.services.trial_service import TrialService


class FakeUser:
    def __init__(self, *, is_official=False, trial_expires_at=None) -> None:
        self.is_official = is_official
        self.trial_expires_at = trial_expires_at


def test_trial_active_for_official() -> None:
    user = FakeUser(is_official=True, trial_expires_at=datetime.now(UTC) - timedelta(hours=1))
    assert TrialService.is_trial_active(user) is True


def test_trial_expired_raises() -> None:
    user = FakeUser(trial_expires_at=datetime.now(UTC) - timedelta(hours=1))
    with pytest.raises(AppError) as exc:
        TrialService.assert_trial_active(user)
    assert exc.value.code == ErrorCode.FORBIDDEN


def test_trial_still_active() -> None:
    user = FakeUser(trial_expires_at=datetime.now(UTC) + timedelta(hours=10))
    TrialService.assert_trial_active(user)
