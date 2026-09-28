from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.match_orders import (
    MatchOrdersParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events, sync_orderbook


async def match_orders(
    ctx: HandlerContext,
    match_orders: TezosTransaction[MatchOrdersParameter, OrderbookStorage],
) -> None:
    # Fills also move fees into the fee ledger and may close market or dust
    # remainders as cancelled
    orderbook = await sync_orderbook(
        ctx, match_orders.data.target_address, match_orders.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=match_orders.storage,
        intent=models.OrderEventType.FILL,
        data=match_orders.data,
    )
