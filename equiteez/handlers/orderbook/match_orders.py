from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.match_orders import MatchOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import register_token
from dateutil import parser

async def match_orders(
    ctx: HandlerContext,
    match_orders: TezosTransaction[MatchOrdersParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address             = match_orders.data.target_address
    fee_ledger          = match_orders.storage.feeLedger
    rwa_order_ledger    = match_orders.storage.rwaOrderLedger
    buy_order_ledger    = match_orders.storage.buyOrderLedger
    sell_order_ledger   = match_orders.storage.sellOrderLedger
    highest_buy_price   = match_orders.storage.highestBuyPrice
    lowest_sell_price   = match_orders.storage.lowestSellPrice
    last_matched_price  = match_orders.storage.lastMatchedPrice

    # Update orderbook
    orderbook           = await models.Orderbook.get(
        address = address
    )
    orderbook.highest_buy_price             = highest_buy_price.price
    orderbook.highest_buy_price_order_id    = highest_buy_price.orderId
    orderbook.lowest_sell_price             = lowest_sell_price.price
    orderbook.lowest_sell_price_order_id    = lowest_sell_price.orderId
    orderbook.last_matched_price            = last_matched_price.price
    orderbook.last_matched_price_timestamp  = parser.parse(last_matched_price.lastMatchedTimestamp) if last_matched_price.lastMatchedTimestamp else None
    await orderbook.save()

    # Update fees
    for currency_name in fee_ledger:
        fee_record      = fee_ledger[currency_name]
        fee_amount      = fee_record.nat_0
        paid_fee        = fee_record.nat_1
        currency, _     = await models.OrderbookCurrency.get_or_create(
            orderbook       = orderbook,
            currency_name   = currency_name
        )
        await currency.save()
        orderbook_fee   = models.OrderbookFee(
            orderbook   = orderbook,
            currency    = currency,
            fee_amount  = fee_amount,
            paid_fee    = paid_fee
        )
        await orderbook_fee.save()

    # Update order
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record    = rwa_order_ledger[rwa_order_token_address]
        buy_price_map       = rwa_order_record.buyPriceMap
        buy_order_map       = rwa_order_record.buyOrderMap
        sell_price_map      = rwa_order_record.sellPriceMap
        sell_order_map      = rwa_order_record.sellOrderMap
        rwa_order_token     = await register_token(
            ctx = ctx,
            address = rwa_order_token_address
        )
        rwa_order           = await models.OrderbookRwaOrder.get(
            orderbook   = orderbook,
            rwa_token   = rwa_order_token
        )
        await rwa_order.save()

        # Delete old records
        await models.OrderbookRwaOrderBuyPrice.filter(
            rwa_order   = rwa_order
        ).all().delete()
        await models.OrderbookRwaOrderBuyOrder.filter(
            rwa_order   = rwa_order
        ).all().delete()
        await models.OrderbookRwaOrderSellPrice.filter(
            rwa_order   = rwa_order
        ).all().delete()
        await models.OrderbookRwaOrderSellOrder.filter(
            rwa_order   = rwa_order
        ).all().delete()

        # Create records
        for buy_price_counter in buy_price_map:
            buy_price               = buy_price_map[buy_price_counter]
            buy_price_record, _     = await models.OrderbookRwaOrderBuyPrice.get_or_create(
                rwa_order   = rwa_order,
                counter     = buy_price_counter
            )
            buy_price_record.price  = buy_price
            await buy_price_record.save()

        for buy_price in buy_order_map:
            buy_order_ids               = buy_order_map[buy_price]
            buy_order_record, _         = await models.OrderbookRwaOrderBuyOrder.get_or_create(
                rwa_order   = rwa_order,
                price       = buy_price
            )
            buy_order_record.order_ids  = buy_order_ids
            await buy_order_record.save()

        for sell_price_counter in sell_price_map:
            sell_price               = sell_price_map[sell_price_counter]
            sell_price_record, _     = await models.OrderbookRwaOrderSellPrice.get_or_create(
                rwa_order   = rwa_order,
                counter     = sell_price_counter
            )
            sell_price_record.price  = sell_price
            await sell_price_record.save()

        for sell_price in sell_order_map:
            sell_order_ids               = sell_order_map[sell_price]
            sell_order_record, _         = await models.OrderbookRwaOrderSellOrder.get_or_create(
                rwa_order   = rwa_order,
                price       = sell_price
            )
            sell_order_record.order_ids  = sell_order_ids
            await sell_order_record.save()

    # Update order ledgers
    for buy_order_id in buy_order_ledger:
        # Get buy order parameters
        buy_order_record                    = buy_order_ledger[buy_order_id]
        fulfilled_amount                    = buy_order_record.fulfilledAmount
        unfulfilled_amount                  = buy_order_record.unfulfilledAmount
        total_paid_out                      = buy_order_record.totalOrderFulfilled.nat_0
        total_usd_value_of_rwa_token_amount = buy_order_record.totalOrderFulfilled.nat_1
        is_fulfilled                        = buy_order_record.booleans.bool_0
        is_canceled                         = buy_order_record.booleans.bool_1
        is_expired                          = buy_order_record.booleans.bool_2
        is_refunded                         = buy_order_record.isRefunded
        refunded_amount                     = buy_order_record.refundedAmount
        order_expiry                        = buy_order_record.orderExpiry
        created_at                          = parser.parse(buy_order_record.orderTimestamps.timestamp_0) if buy_order_record.orderTimestamps.timestamp_0 else None
        ended_at                            = parser.parse(buy_order_record.orderTimestamps.timestamp_1) if buy_order_record.orderTimestamps.timestamp_1 else None

        # Save buy order
        buy_order                           = await models.OrderbookOrder.get(
            orderbook   = orderbook,
            order_type  = models.OrderType.BUY,
            order_id    = buy_order_id
        )
        buy_order.fulfilled_amount                        = fulfilled_amount
        buy_order.unfulfilled_amount                      = unfulfilled_amount
        buy_order.total_paid_out                          = total_paid_out
        buy_order.total_usd_value_of_rwa_token_amount     = total_usd_value_of_rwa_token_amount
        buy_order.is_fulfilled                            = is_fulfilled
        buy_order.is_canceled                             = is_canceled
        buy_order.is_expired                              = is_expired
        buy_order.is_refunded                             = is_refunded
        buy_order.refunded_amount                         = refunded_amount
        buy_order.order_expiry                            = order_expiry
        buy_order.created_at                              = created_at
        buy_order.ended_at                                = ended_at
        await buy_order.save()

    for sell_order_id in sell_order_ledger:
        # Get buy order parameters
        sell_order_record                   = sell_order_ledger[sell_order_id]
        fulfilled_amount                    = sell_order_record.fulfilledAmount
        unfulfilled_amount                  = sell_order_record.unfulfilledAmount
        total_paid_out                      = sell_order_record.totalOrderFulfilled.nat_0
        total_usd_value_of_rwa_token_amount = sell_order_record.totalOrderFulfilled.nat_1
        is_fulfilled                        = sell_order_record.booleans.bool_0
        is_canceled                         = sell_order_record.booleans.bool_1
        is_expired                          = sell_order_record.booleans.bool_2
        is_refunded                         = sell_order_record.isRefunded
        refunded_amount                     = sell_order_record.refundedAmount
        order_expiry                        = sell_order_record.orderExpiry
        created_at                          = parser.parse(sell_order_record.orderTimestamps.timestamp_0) if sell_order_record.orderTimestamps.timestamp_0 else None
        ended_at                            = parser.parse(sell_order_record.orderTimestamps.timestamp_1) if sell_order_record.orderTimestamps.timestamp_1 else None

        # Save buy order
        sell_order                           = await models.OrderbookOrder.get(
            orderbook   = orderbook,
            order_type  = models.OrderType.SELL,
            order_id    = sell_order_id
        )
        sell_order.fulfilled_amount                        = fulfilled_amount
        sell_order.unfulfilled_amount                      = unfulfilled_amount
        sell_order.total_paid_out                          = total_paid_out
        sell_order.total_usd_value_of_rwa_token_amount     = total_usd_value_of_rwa_token_amount
        sell_order.is_fulfilled                            = is_fulfilled
        sell_order.is_canceled                             = is_canceled
        sell_order.is_expired                              = is_expired
        sell_order.is_refunded                             = is_refunded
        sell_order.refunded_amount                         = refunded_amount
        sell_order.order_expiry                            = order_expiry
        sell_order.created_at                              = created_at
        sell_order.ended_at                                = ended_at
        await sell_order.save()
