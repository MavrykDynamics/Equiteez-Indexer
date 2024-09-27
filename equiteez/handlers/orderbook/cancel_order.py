from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.cancel_order import CancelOrderParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def cancel_order(
    ctx: HandlerContext,
    cancel_order: TezosTransaction[CancelOrderParameter, OrderbookStorage],
) -> None:
    ...