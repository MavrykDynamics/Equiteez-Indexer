from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.process_refund import (
    ProcessRefundParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


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
    for buy_order_id in buy_order_ledger:
        # Get buy order parameters
        buy_order_record = buy_order_ledger[buy_order_id]
        is_refunded = buy_order_record.isRefunded
        refunded_amount = buy_order_record.refundedAmount

        # Save buy order
        buy_order = await models.OrderbookOrder.get(
            orderbook=orderbook, order_type=models.OrderType.BUY, order_id=buy_order_id
        )
        buy_order.is_refunded = is_refunded
        buy_order.refunded_amount = refunded_amount
        await buy_order.save()

    for sell_order_id in sell_order_ledger:
        # Get sell order parameters
        sell_order_record = sell_order_ledger[sell_order_id]
        is_refunded = sell_order_record.isRefunded
        refunded_amount = sell_order_record.refundedAmount

        # Save sell order
        sell_order = await models.OrderbookOrder.get(
            orderbook=orderbook,
            order_type=models.OrderType.SELL,
            order_id=sell_order_id,
        )
        sell_order.is_refunded = is_refunded
        sell_order.refunded_amount = refunded_amount
        await sell_order.save()
