from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.clear_expired_orders import ClearExpiredOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import register_token


async def clear_expired_orders(
    ctx: HandlerContext,
    clear_expired_orders: TezosTransaction[ClearExpiredOrdersParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address             = clear_expired_orders.data.target_address
    highest_buy_price   = clear_expired_orders.storage.highestBuyPrice
    lowest_sell_price   = clear_expired_orders.storage.lowestSellPrice
    buy_order_ledger    = clear_expired_orders.storage.buyOrderLedger
    sell_order_ledger   = clear_expired_orders.storage.sellOrderLedger
    rwa_order_ledger    = clear_expired_orders.storage.rwaOrderLedger

    # Update orderbook
    orderbook   = await models.Orderbook.get(
        address = address
    )
    orderbook.highest_buy_price             = highest_buy_price.price
    orderbook.highest_buy_price_order_id    = highest_buy_price.orderId
    orderbook.lowest_sell_price             = lowest_sell_price.price
    orderbook.lowest_sell_price_order_id    = lowest_sell_price.orderId
    await orderbook.save()

    # Update records
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
        rwa_order, _        = await models.OrderbookRwaOrder.get_or_create(
            orderbook   = orderbook,
            rwa_token   = rwa_order_token
        )
        await rwa_order.save()

        # Delete past orders and prices
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

        # Recreate new prices and orders
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

    # Save buy and sell orders
    for buy_order_id in buy_order_ledger:
        # Get buy order parameters
        buy_order_record                    = buy_order_ledger[buy_order_id]
        order_type                          = models.OrderType.BUY
        is_expired                          = buy_order_record.booleans.bool_2

        # Save buy order
        buy_order                           = await models.OrderbookOrder.get(
            orderbook                               = orderbook,
            order_id                                = buy_order_id,
            order_type                              = order_type
        )
        buy_order.is_expired                = is_expired
        await buy_order.save()

    for sell_order_id in sell_order_ledger:
        # Get sell order parameters
        sell_order_record                   = sell_order_ledger[sell_order_id]
        order_type                          = models.OrderType.SELL
        is_expired                          = sell_order_record.booleans.bool_2

        # Save sell order
        sell_order                          = await models.OrderbookOrder.get(
            orderbook                               = orderbook,
            order_id                                = sell_order_id,
            order_type                              = order_type
        )
        sell_order.is_expired               = is_expired
        await sell_order.save()
