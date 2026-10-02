from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_buy_order import (
    PlaceBuyOrderParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events


async def place_buy_order(
    ctx: HandlerContext,
    place_buy_order: TezosTransaction[PlaceBuyOrderParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = place_buy_order.data.target_address
    highest_buy_price = place_buy_order.storage.highestBuyPrice
    buy_order_counter = place_buy_order.storage.buyOrderCounter
    buy_order_ledger = place_buy_order.storage.buyOrderLedger
    rwa_order_ledger = place_buy_order.storage.rwaOrderLedger

    # Update orderbook
    orderbook = await models.Orderbook.get(address=address)
    orderbook.highest_buy_price = highest_buy_price.price
    orderbook.highest_buy_price_order_id = highest_buy_price.orderId
    orderbook.highest_buy_price_market_order_exists = (
        highest_buy_price.marketOrderExists
    )
    orderbook.buy_order_counter = buy_order_counter
    await orderbook.save()

    # Create records
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record = rwa_order_ledger[rwa_order_token_address]
        buy_price_map = rwa_order_record.buyPriceMap
        buy_order_map = rwa_order_record.buyOrderMap
        rwa_order_token, _ = await models.Token.get_or_create(
            address=rwa_order_token_address
        )
        rwa_order, _ = await models.OrderbookRwaOrder.get_or_create(
            orderbook=orderbook, rwa_token=rwa_order_token
        )

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

    # Save placed buy orders
    await record_order_events(
        ctx,
        orderbook=orderbook,
        ledgers=[(models.OrderType.BUY, buy_order_ledger)],
        intent=models.OrderEventType.PLACE,
        data=place_buy_order.data,
    )
