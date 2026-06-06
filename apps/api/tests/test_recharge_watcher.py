import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from kairox_api.features.recharge.watcher import deposit_watcher_loop


@pytest.mark.asyncio
async def test_deposit_watcher_runs_cycle() -> None:
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_container = AsyncMock()
    mock_container.recharge.run_watcher_cycle = AsyncMock()

    with (
        patch("kairox_api.features.recharge.watcher.SessionLocal", return_value=mock_session),
        patch("kairox_api.features.recharge.watcher.build_container", return_value=mock_container),
        patch("asyncio.sleep", new=AsyncMock(side_effect=asyncio.CancelledError)),
        pytest.raises(asyncio.CancelledError),
    ):
        await deposit_watcher_loop()

    mock_container.recharge.run_watcher_cycle.assert_awaited()
