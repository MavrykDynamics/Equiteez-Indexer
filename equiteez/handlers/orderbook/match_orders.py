from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.match_orders import MatchOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_order_events
from dateutil import parser


async def match_orders(
    ctx: HandlerContext,
    match_orders: TezosTransaction[MatchOrdersParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address = match_orders.data.target_address
    fee_ledger = match_orders.storage.feeLedger
    rwa_order_ledger = match_orders.storage.rwaOrderLedger
    buy_order_ledger = match_orders.storage.buyOrderLedger
    sell_order_ledger = match_orders.storage.sellOrderLedger
    highest_buy_price = match_orders.storage.highestBuyPrice
    lowest_sell_price = match_orders.storage.lowestSellPrice
    last_matched_price = match_orders.storage.lastMatchedPrice

    # Update orderbook
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
    orderbook.last_matched_price = last_matched_price.price
    orderbook.last_matched_price_timestamp = (
        parser.parse(last_matched_price.lastMatchedTimestamp)
        if last_matched_price.lastMatchedTimestamp
        else None
    )
    await orderbook.save()

    # Update fees
    for currency_name in fee_ledger:
        fee_record = fee_ledger[currency_name]
        fee_amount = fee_record.nat_0
        paid_fee = fee_record.nat_1
        currency, _ = await models.OrderbookCurrency.get_or_create(
            orderbook=orderbook, currency_name=currency_name
        )
        orderbook_fee, _ = await models.OrderbookFee.get_or_create(
            orderbook=orderbook, currency=currency
        )
        orderbook_fee.fee_amount = fee_amount
        orderbook_fee.paid_fee = paid_fee
        await orderbook_fee.save()

    # Update order
    for rwa_order_token_address in rwa_order_ledger:
        rwa_order_record = rwa_order_ledger[rwa_order_token_address]
        buy_price_map = rwa_order_record.buyPriceMap
        buy_order_map = rwa_order_record.buyOrderMap
        sell_price_map = rwa_order_record.sellPriceMap
        sell_order_map = rwa_order_record.sellOrderMap
        rwa_order_token, _ = await models.Token.get_or_create(
            address=rwa_order_token_address
        )
        rwa_order = await models.OrderbookRwaOrder.get(
            orderbook=orderbook, rwa_token=rwa_order_token
        )

        # Delete old records
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

        # Create records
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

    # Update order ledgers
    await record_order_events(
        ctx,
        orderbook=orderbook,
        ledgers=[
            (models.OrderType.BUY, buy_order_ledger),
            (models.OrderType.SELL, sell_order_ledger),
        ],
        intent=models.OrderEventType.FILL,
        data=match_orders.data,
    )
