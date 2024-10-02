from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, OrderbookStorage],
) -> None:
    breakpoint()