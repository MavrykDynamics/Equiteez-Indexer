from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_buy_order import PlaceBuyOrderParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import register_token
from dateutil import parser 

async def place_buy_order(
    ctx: HandlerContext,
    place_buy_order: TezosTransaction[PlaceBuyOrderParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address             = place_buy_order.data.target_address
    highest_buy_price   = place_buy_order.storage.highestBuyPrice
    buy_order_counter   = place_buy_order.storage.buyOrderCounter
    buy_order_ledger    = place_buy_order.storage.buyOrderLedger
    rwa_order_ledger    = place_buy_order.storage.rwaOrderLedger

    # Update orderbook
    orderbook   = await models.Orderbook.get(
        address = address
    )
    orderbook.highest_buy_price             = highest_buy_price.price
    orderbook.highest_buy_price_order_id    = highest_buy_price.orderId
    orderbook.buy_order_counter             = buy_order_counter
    await orderbook.save()

    # Create records
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record    = rwa_order_ledger[rwa_order_token_address]
        buy_price_map       = rwa_order_record.buyPriceMap
        buy_order_map       = rwa_order_record.buyOrderMap
        rwa_order_token     = await register_token(
            ctx = ctx,
            address = rwa_order_token_address
        )
        rwa_order, _        = await models.OrderbookRwaOrder.get_or_create(
            orderbook   = orderbook,
            rwa_token   = rwa_order_token
        )
        await rwa_order.save()

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

    for buy_order_id in buy_order_ledger:
        # Get buy order parameters
        buy_order_record                    = buy_order_ledger[buy_order_id]
        order_type                          = models.OrderType.BUY if buy_order_record.orderType == "BUY" else models.OrderType.SELL
        initiator                           = buy_order_record.initiator
        rwa_token_amount                    = buy_order_record.rwaTokenAmount
        price_per_rwa_token                 = buy_order_record.pricePerRwaToken
        currency_name                       = buy_order_record.currency
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
        
        # Get currency
        currency, _                         = await models.OrderbookCurrency.get_or_create(
            orderbook       = orderbook,
            currency_name   = currency_name
        )
        await currency.save()

        # Save buy order
        buy_order                           = models.OrderbookOrder(
            orderbook                               = orderbook,
            currency                                = currency,
            order_id                                = buy_order_id,
            order_type                              = order_type,
            initiator                               = initiator,
            rwa_token_amount                        = rwa_token_amount,
            price_per_rwa_token                     = price_per_rwa_token,
            fulfilled_amount                        = fulfilled_amount,
            unfulfilled_amount                      = unfulfilled_amount,
            total_paid_out                          = total_paid_out,
            total_usd_value_of_rwa_token_amount     = total_usd_value_of_rwa_token_amount,
            is_fulfilled                            = is_fulfilled,
            is_canceled                             = is_canceled,
            is_expired                              = is_expired,
            is_refunded                             = is_refunded,
            refunded_amount                         = refunded_amount,
            order_expiry                            = order_expiry,
            created_at                              = created_at,
            ended_at                                = ended_at
        )
        await buy_order.save()
