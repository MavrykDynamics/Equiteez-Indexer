from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.process_refund import (
    ProcessRefundParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events


async def process_refund(
    ctx: HandlerContext,
    process_refund: TezosTransaction[ProcessRefundParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = process_refund.data.target_address
    buy_order_ledger = process_refund.storage.buyOrderLedger
    sell_order_ledger = process_refund.storage.sellOrderLedger

    # Update orderbook
    orderbook = await models.Orderbook.get(address=address)

    # Update records
    await record_order_events(
        ctx,
        orderbook=orderbook,
        ledgers=[
            (models.OrderType.BUY, buy_order_ledger),
            (models.OrderType.SELL, sell_order_ledger),
        ],
        intent=models.OrderEventType.REFUND,
        data=process_refund.data,
    )
