import logging

from dipdup.context import HookContext
from tortoise import Tortoise

logger = logging.getLogger(__name__)


async def refresh_rwa_volume(ctx: HookContext) -> None:
    conn = Tortoise.get_connection("default")
    await conn.execute_query(
        "REFRESH MATERIALIZED VIEW CONCURRENTLY rwa_volume_24h_tokens"
    )
    logger.debug("Refreshed rwa_volume_24h_tokens")
