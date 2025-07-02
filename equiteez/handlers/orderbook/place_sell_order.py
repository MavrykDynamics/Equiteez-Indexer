from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_sell_order import PlaceSellOrderParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from dateutil import parser 

async def place_sell_order(
    ctx: HandlerContext,
    place_sell_order: TezosTransaction[PlaceSellOrderParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address             = place_sell_order.data.target_address
    lowest_sell_price   = place_sell_order.storage.lowestSellPrice
    sell_order_counter  = place_sell_order.storage.sellOrderCounter
    sell_order_ledger   = place_sell_order.storage.sellOrderLedger
    rwa_order_ledger    = place_sell_order.storage.rwaOrderLedger

    # Update orderbook
    orderbook   = await models.Orderbook.get(
        address = address
    )
    orderbook.lowest_sell_price             = lowest_sell_price.price
    orderbook.lowest_sell_price_order_id    = lowest_sell_price.orderId
    orderbook.sell_order_counter            = sell_order_counter
    await orderbook.save()

    # Create records
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record    = rwa_order_ledger[rwa_order_token_address]
        sell_price_map      = rwa_order_record.sellPriceMap
        sell_order_map      = rwa_order_record.sellOrderMap
        rwa_order_token, _  = await models.Token.get_or_create(
            address = rwa_order_token_address
        )
        await rwa_order_token.save()
        rwa_order, _        = await models.OrderbookRwaOrder.get_or_create(
            orderbook   = orderbook,
            rwa_token   = rwa_order_token
        )
        await rwa_order.save()

        for sell_price_counter in sell_price_map:
            sell_price               = sell_price_map[sell_price_counter]
            sell_price_record, _     = await models.OrderbookRwaOrderSellPrice.get_or_create(
                rwa_order   = rwa_order,
                counter     = sell_price_counter
            )
            sell_price_record.price  = sell_price
            await sell_price_record.save()

        for sell_price in sell_order_map:
            sell_order_ids              = sell_order_map[sell_price]
            sell_order_ids_int          = [int(x) for x in sell_order_ids]
            sell_order_record, _        = await models.OrderbookRwaOrderSellOrder.get_or_create(
                rwa_order   = rwa_order,
                price       = sell_price
            )
            sell_order_record.order_ids  = sell_order_ids_int
            await sell_order_record.save()

    for sell_order_id in sell_order_ledger:
        # Get sell order parameters
        sell_order_record                   = sell_order_ledger[sell_order_id]
        order_type                          = models.OrderType.SELL
        initiator                           = sell_order_record.initiator
        rwa_token_amount                    = sell_order_record.rwaTokenAmount
        price_per_rwa_token                 = sell_order_record.pricePerRwaToken
        currency_name                       = sell_order_record.currency
        fulfilled_amount                    = sell_order_record.fulfilledAmount
        unfulfilled_amount                  = sell_order_record.unfulfilledAmount
        total_paid_out                      = sell_order_record.totalOrderFulfilled.nat_0
        total_usd_value_of_rwa_token_amount = sell_order_record.totalOrderFulfilled.nat_1
        is_fulfilled                        = sell_order_record.booleans.bool_0
        is_canceled                         = sell_order_record.booleans.bool_1
        is_expired                          = sell_order_record.booleans.bool_2
        is_refunded                         = sell_order_record.isRefunded
        refunded_amount                     = sell_order_record.refundedAmount
        order_expiry                        = parser.parse(sell_order_record.orderExpiry)
        
        # Get currency
        currency, _                         = await models.OrderbookCurrency.get_or_create(
            orderbook       = orderbook,
            currency_name   = currency_name
        )
        await currency.save()

        # Create initiator
        user, _                             = await models.EquiteezUser.get_or_create(
            address = initiator
        )
        await user.save()

        # Save sell order
        sell_order                          = models.OrderbookOrder(
            orderbook                               = orderbook,
            currency                                = currency,
            order_id                                = sell_order_id,
            order_type                              = order_type,
            initiator                               = user,
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
            order_expiry                            = order_expiry
        )
        if sell_order_record.orderTimestamps.timestamp_0:
            sell_order.created_at    = parser.parse(sell_order_record.orderTimestamps.timestamp_0)
        if sell_order_record.orderTimestamps.timestamp_1:
            sell_order.ended_at      = parser.parse(sell_order_record.orderTimestamps.timestamp_1)
        await sell_order.save()
