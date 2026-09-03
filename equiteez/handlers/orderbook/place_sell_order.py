from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_sell_order import (
    PlaceSellOrderParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events


async def place_sell_order(
    ctx: HandlerContext,
    place_sell_order: TezosTransaction[PlaceSellOrderParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = place_sell_order.data.target_address
    lowest_sell_price = place_sell_order.storage.lowestSellPrice
    sell_order_counter = place_sell_order.storage.sellOrderCounter
    sell_order_ledger = place_sell_order.storage.sellOrderLedger
    rwa_order_ledger = place_sell_order.storage.rwaOrderLedger

    # Update orderbook
    orderbook = await models.Orderbook.get(address=address)
    orderbook.lowest_sell_price = lowest_sell_price.price
    orderbook.lowest_sell_price_order_id = lowest_sell_price.orderId
    orderbook.lowest_sell_price_market_order_exists = (
        lowest_sell_price.marketOrderExists
    )
    orderbook.sell_order_counter = sell_order_counter
    await orderbook.save()

    # Create records
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record = rwa_order_ledger[rwa_order_token_address]
        sell_price_map = rwa_order_record.sellPriceMap
        sell_order_map = rwa_order_record.sellOrderMap
        rwa_order_token, _ = await models.Token.get_or_create(
            address=rwa_order_token_address
        )
        rwa_order, _ = await models.OrderbookRwaOrder.get_or_create(
            orderbook=orderbook, rwa_token=rwa_order_token
        )

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

    # Save placed sell orders
    await record_order_events(
        ctx,
        orderbook=orderbook,
        ledgers=[(models.OrderType.SELL, sell_order_ledger)],
        intent=models.OrderEventType.PLACE,
        data=place_sell_order.data,
    )
