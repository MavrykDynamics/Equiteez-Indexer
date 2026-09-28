from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.cancel_orders import (
    CancelOrdersParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events, sync_orderbook


async def cancel_orders(
    ctx: HandlerContext,
    cancel_orders: TezosTransaction[CancelOrdersParameter, OrderbookStorage],
) -> None:
    # Cancelling refunds the escrow net of cancelOrderFee (fee ledger) and
    # removes the orders from the book
    orderbook = await sync_orderbook(
        ctx, cancel_orders.data.target_address, cancel_orders.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=cancel_orders.storage,
        intent=models.OrderEventType.CANCEL,
        data=cancel_orders.data,
    )
