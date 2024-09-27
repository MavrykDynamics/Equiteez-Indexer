from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.clear_expired_orders import ClearExpiredOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def clear_expired_orders(
    ctx: HandlerContext,
    clear_expired_orders: TezosTransaction[ClearExpiredOrdersParameter, OrderbookStorage],
) -> None:
    ...