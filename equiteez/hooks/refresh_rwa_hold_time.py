import logging

from dipdup.context import HookContext
from tortoise import Tortoise

logger = logging.getLogger(__name__)


async def refresh_rwa_hold_time(ctx: HookContext) -> None:
    conn = Tortoise.get_connection("default")
    await conn.execute_query(
        "REFRESH MATERIALIZED VIEW CONCURRENTLY token_avg_hold_time"
    )
    logger.debug("Refreshed token_avg_hold_time")
