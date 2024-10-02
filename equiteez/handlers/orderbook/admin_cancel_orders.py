from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.admin_cancel_orders import AdminCancelOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from dateutil import parser

async def admin_cancel_orders(
    ctx: HandlerContext,
    admin_cancel_orders: TezosTransaction[AdminCancelOrdersParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address             = admin_cancel_orders.data.target_address
    buy_order_ledger    = admin_cancel_orders.storage.buyOrderLedger
    sell_order_ledger   = admin_cancel_orders.storage.sellOrderLedger

    # Get orderbook
    orderbook           = await models.Orderbook.get(
        address = address
    )

    # Update orders
    for buy_order_id in buy_order_ledger:
        # Get buy order parameters
        buy_order_record                    = buy_order_ledger[buy_order_id]
        is_fulfilled                        = buy_order_record.booleans.bool_0
        is_canceled                         = buy_order_record.booleans.bool_1
        is_expired                          = buy_order_record.booleans.bool_2
        is_refunded                         = buy_order_record.isRefunded
        refunded_amount                     = buy_order_record.refundedAmount
        order_expiry                        = buy_order_record.orderExpiry
        ended_at                            = parser.parse(buy_order_record.orderTimestamps.timestamp_1) if buy_order_record.orderTimestamps.timestamp_1 else None

        # Save buy order
        buy_order                           = await models.OrderbookOrder.get(
            orderbook   = orderbook,
            order_type  = models.OrderType.BUY,
            order_id    = buy_order_id
        )
        buy_order.is_fulfilled                            = is_fulfilled
        buy_order.is_canceled                             = is_canceled
        buy_order.is_expired                              = is_expired
        buy_order.is_refunded                             = is_refunded
        buy_order.refunded_amount                         = refunded_amount
        buy_order.order_expiry                            = order_expiry
        buy_order.ended_at                                = ended_at
        await buy_order.save()

    for sell_order_id in sell_order_ledger:
        # Get buy order parameters
        sell_order_record                   = sell_order_ledger[sell_order_id]
        is_fulfilled                        = sell_order_record.booleans.bool_0
        is_canceled                         = sell_order_record.booleans.bool_1
        is_expired                          = sell_order_record.booleans.bool_2
        is_refunded                         = sell_order_record.isRefunded
        refunded_amount                     = sell_order_record.refundedAmount
        order_expiry                        = sell_order_record.orderExpiry
        ended_at                            = parser.parse(sell_order_record.orderTimestamps.timestamp_1) if sell_order_record.orderTimestamps.timestamp_1 else None

        # Save buy order
        sell_order                           = await models.OrderbookOrder.get(
            orderbook   = orderbook,
            order_type  = models.OrderType.SELL,
            order_id    = sell_order_id
        )
        sell_order.is_fulfilled                            = is_fulfilled
        sell_order.is_canceled                             = is_canceled
        sell_order.is_expired                              = is_expired
        sell_order.is_refunded                             = is_refunded
        sell_order.refunded_amount                         = refunded_amount
        sell_order.order_expiry                            = order_expiry
        sell_order.ended_at                                = ended_at
        await sell_order.save()
