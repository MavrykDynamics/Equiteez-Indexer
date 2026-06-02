import logging

from dipdup.context import HookContext
from tortoise import Tortoise

logger = logging.getLogger(__name__)


async def refresh_launchpad_stats(ctx: HookContext) -> None:
    conn = Tortoise.get_connection("default")
    await conn.execute_query(
        "REFRESH MATERIALIZED VIEW CONCURRENTLY launchpad_launch_stats"
    )
    logger.debug("Refreshed launchpad_launch_stats")
