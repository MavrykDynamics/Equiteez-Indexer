from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_buy_order import (
    PlaceBuyOrderParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events, sync_orderbook


async def place_buy_order(
    ctx: HandlerContext,
    place_buy_order: TezosTransaction[PlaceBuyOrderParameter, OrderbookStorage],
) -> None:
    # Placement only rests the order; matching is matchOrders' job
    orderbook = await sync_orderbook(
        ctx, place_buy_order.data.target_address, place_buy_order.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=place_buy_order.storage,
        intent=models.OrderEventType.PLACE,
        data=place_buy_order.data,
    )
