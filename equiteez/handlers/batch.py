from collections.abc import Iterable
from dipdup.context import HandlerContext
from dipdup.index import MatchedHandler

from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.utils.rwa_supply import sync_token_supply


async def batch(ctx: HandlerContext, handlers: Iterable[MatchedHandler]) -> None:
    handlers = list(handlers)
    if handlers and handlers[0].index.name == "rwa_index":
        # DipDup groups matches by callback within an operation group. Replay
        # token and launchpad changes in chain order, including internal calls.
        handlers.sort(
            key=lambda h: next(iter(h.args)).data.id
            if hasattr(next(iter(h.args)), "data")
            else next(iter(h.args)).id
        )
        seen = set()
        for handler in handlers:
            for arg in handler.args:
                if isinstance(getattr(arg, "storage", None), BaseTokenStorage):
                    if arg.data.id not in seen:
                        await sync_token_supply(arg.data)
                        seen.add(arg.data.id)
            await ctx.fire_matched_handler(handler)
    else:
        for handler in handlers:
            await ctx.fire_matched_handler(handler)
