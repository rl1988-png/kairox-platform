import asyncio
import logging

from kairox_api.config.settings import settings
from kairox_api.constants.limits import RECHARGE_POLL_INTERVAL_SECONDS
from kairox_api.core.database import SessionLocal
from kairox_api.dependencies.container import build_container

logger = logging.getLogger(__name__)


async def deposit_watcher_loop() -> None:
    """Poll TronGrid for pending recharge orders — retry-safe background task."""
    while True:
        try:
            async with SessionLocal() as session:
                container = build_container(session)
                await container.recharge.run_watcher_cycle()
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Deposit watcher cycle failed")
        await asyncio.sleep(RECHARGE_POLL_INTERVAL_SECONDS)


def start_deposit_watcher() -> asyncio.Task[None] | None:
    if not settings.recharge_watcher_enabled:
        return None
    return asyncio.create_task(deposit_watcher_loop())
