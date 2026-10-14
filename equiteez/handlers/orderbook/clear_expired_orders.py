from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.clear_expired_orders import (
    ClearExpiredOrdersParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events, sync_orderbook


async def clear_expired_orders(
    ctx: HandlerContext,
    clear_expired_orders: TezosTransaction[
        ClearExpiredOrdersParameter, OrderbookStorage
    ],
) -> None:
    # Flags orders expired and removes them from the book; escrow stays until
    # processRefund
    orderbook = await sync_orderbook(
        ctx, clear_expired_orders.data.target_address, clear_expired_orders.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=clear_expired_orders.storage,
        intent=models.OrderEventType.EXPIRE,
        data=clear_expired_orders.data,
    )
