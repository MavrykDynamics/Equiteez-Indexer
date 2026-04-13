import logging

from dipdup.context import HookContext

from equiteez.utils.indexed_addresses import get_indexed_addresses

logger = logging.getLogger(__name__)


async def on_restart(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql("on_restart")
    await get_indexed_addresses()
    logger.info("on_restart: warmed indexed_addresses cache")
