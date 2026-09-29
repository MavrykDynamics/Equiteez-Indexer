from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.process_refund import (
    ProcessRefundParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events, sync_orderbook


async def process_refund(
    ctx: HandlerContext,
    process_refund: TezosTransaction[ProcessRefundParameter, OrderbookStorage],
) -> None:
    orderbook = await sync_orderbook(
        ctx, process_refund.data.target_address, process_refund.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=process_refund.storage,
        intent=models.OrderEventType.REFUND,
        data=process_refund.data,
    )
