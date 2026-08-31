from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.cancel_orders import (
    CancelOrdersParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events


async def cancel_orders(
    ctx: HandlerContext,
    cancel_orders: TezosTransaction[CancelOrdersParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = cancel_orders.data.target_address
    highest_buy_price = cancel_orders.storage.highestBuyPrice
    lowest_sell_price = cancel_orders.storage.lowestSellPrice
    buy_order_ledger = cancel_orders.storage.buyOrderLedger
    sell_order_ledger = cancel_orders.storage.sellOrderLedger
    rwa_order_ledger = cancel_orders.storage.rwaOrderLedger

    # Update orderbook (cancelling removes orders from the orderbook and
    # recalculates the best buy/sell prices)
    orderbook = await models.Orderbook.get(address=address)
    orderbook.highest_buy_price = highest_buy_price.price
    orderbook.highest_buy_price_order_id = highest_buy_price.orderId
    orderbook.highest_buy_price_market_order_exists = (
        highest_buy_price.marketOrderExists
    )
    orderbook.lowest_sell_price = lowest_sell_price.price
    orderbook.lowest_sell_price_order_id = lowest_sell_price.orderId
    orderbook.lowest_sell_price_market_order_exists = (
        lowest_sell_price.marketOrderExists
    )
    await orderbook.save()

    # Update records (cancelled orders are removed from the price/order maps)
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record = rwa_order_ledger[rwa_order_token_address]
        buy_price_map = rwa_order_record.buyPriceMap
        buy_order_map = rwa_order_record.buyOrderMap
        sell_price_map = rwa_order_record.sellPriceMap
        sell_order_map = rwa_order_record.sellOrderMap
        rwa_order_token, _ = await models.Token.get_or_create(
            address=rwa_order_token_address
        )
        rwa_order, _ = await models.OrderbookRwaOrder.get_or_create(
            orderbook=orderbook, rwa_token=rwa_order_token
        )

        # Delete past orders and prices
        await (
            models.OrderbookRwaOrderBuyPrice.filter(rwa_order=rwa_order).all().delete()
        )
        await (
            models.OrderbookRwaOrderBuyOrder.filter(rwa_order=rwa_order).all().delete()
        )
        await (
            models.OrderbookRwaOrderSellPrice.filter(rwa_order=rwa_order).all().delete()
        )
        await (
            models.OrderbookRwaOrderSellOrder.filter(rwa_order=rwa_order).all().delete()
        )

        # Recreate new prices and orders
        for buy_price_counter in buy_price_map:
            buy_price = buy_price_map[buy_price_counter]
            buy_price_record, _ = await models.OrderbookRwaOrderBuyPrice.get_or_create(
                rwa_order=rwa_order, counter=buy_price_counter
            )
            buy_price_record.price = buy_price
            await buy_price_record.save()

        for buy_price in buy_order_map:
            buy_order_ids = buy_order_map[buy_price]
            buy_order_ids_int = [int(x) for x in buy_order_ids]
            buy_order_record, _ = await models.OrderbookRwaOrderBuyOrder.get_or_create(
                rwa_order=rwa_order, price=buy_price
            )
            buy_order_record.order_ids = buy_order_ids_int
            await buy_order_record.save()

        for sell_price_counter in sell_price_map:
            sell_price = sell_price_map[sell_price_counter]
            (
                sell_price_record,
                _,
            ) = await models.OrderbookRwaOrderSellPrice.get_or_create(
                rwa_order=rwa_order, counter=sell_price_counter
            )
            sell_price_record.price = sell_price
            await sell_price_record.save()

        for sell_price in sell_order_map:
            sell_order_ids = sell_order_map[sell_price]
            sell_order_ids_int = [int(x) for x in sell_order_ids]
            (
                sell_order_record,
                _,
            ) = await models.OrderbookRwaOrderSellOrder.get_or_create(
                rwa_order=rwa_order, price=sell_price
            )
            sell_order_record.order_ids = sell_order_ids_int
            await sell_order_record.save()

    # Update orders
    await record_order_events(
        ctx,
        orderbook=orderbook,
        ledgers=[
            (models.OrderType.BUY, buy_order_ledger),
            (models.OrderType.SELL, sell_order_ledger),
        ],
        intent=models.OrderEventType.CANCEL,
        data=cancel_orders.data,
    )
