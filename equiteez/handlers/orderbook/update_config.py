from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.update_config import UpdateConfigParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, OrderbookStorage],
) -> None:
    breakpoint()