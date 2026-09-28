from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime

from dateutil import parser
from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOperationData

from equiteez import models as models
from equiteez.types.orderbook.tezos_storage import (
    BuyOrderLedger,
    Config,
    OrderbookStorage,
    SellOrderLedger,
)
from equiteez.utils.permits import permit_action
from equiteez.utils.utils import register_token

OrderLedger = BuyOrderLedger | SellOrderLedger
IntentResolver = Callable[["models.OrderType", int], "models.OrderEventType"]


###
# Orderbook-level state
###


def apply_orderbook_config(orderbook: "models.Orderbook", config: Config) -> None:
    orderbook.tick_size = int(config.priceTickSize)
    orderbook.quantity_tick_size = int(config.quantityTickSize)
    orderbook.max_orders_per_price_level = int(config.maxOrdersPerPriceLevel)
    orderbook.min_expiry_time = int(config.minExpiryTime)
    orderbook.min_time_before_closing_order = int(config.minTimeBeforeClosingOrder)
    orderbook.min_buy_order_amount = int(config.minBuyOrderAmount)
    orderbook.min_buy_order_value = int(config.minBuyOrderValue)
    orderbook.min_sell_order_amount = int(config.minSellOrderAmount)
    orderbook.min_sell_order_value = int(config.minSellOrderValue)
    orderbook.buy_order_fee = int(config.buyOrderFee)
    orderbook.sell_order_fee = int(config.sellOrderFee)
    orderbook.cancel_order_fee = int(config.cancelOrderFee)
    orderbook.lower_bound_buy_order_percent = int(config.lowerBoundBuyOrderPercent)
    orderbook.upper_bound_buy_order_percent = int(config.upperBoundBuyOrderPercent)
    orderbook.lower_bound_sell_order_percent = int(config.lowerBoundSellOrderPercent)
    orderbook.upper_bound_sell_order_percent = int(config.upperBoundSellOrderPercent)
    orderbook.permit_default_expiry_duration = int(config.permitDefaultExpiryDuration)
    orderbook.permit_max_expiry_duration = int(config.permitMaxExpiryDuration)


def apply_orderbook_market_state(
    orderbook: "models.Orderbook", storage: OrderbookStorage
) -> None:
    """Best prices, counters and last matched price: plain storage values, so
    every operation carries their full post-state."""
    highest_buy_price = storage.highestBuyPrice
    lowest_sell_price = storage.lowestSellPrice
    last_matched_price = storage.lastMatchedPrice

    orderbook.highest_buy_price = int(highest_buy_price.price)
    orderbook.highest_buy_price_order_id = int(highest_buy_price.orderId)
    orderbook.highest_buy_price_market_order_exists = (
        highest_buy_price.marketOrderExists
    )
    orderbook.lowest_sell_price = int(lowest_sell_price.price)
    orderbook.lowest_sell_price_order_id = int(lowest_sell_price.orderId)
    orderbook.lowest_sell_price_market_order_exists = (
        lowest_sell_price.marketOrderExists
    )
    orderbook.last_matched_price = int(last_matched_price.price)
    orderbook.last_matched_price_timestamp = (
        parser.parse(last_matched_price.lastMatchedTimestamp)
        if last_matched_price.lastMatchedTimestamp
        else None
    )
    orderbook.buy_order_counter = int(storage.buyOrderCounter)
    orderbook.sell_order_counter = int(storage.sellOrderCounter)


async def sync_currencies(
    ctx: HandlerContext, orderbook: "models.Orderbook", storage: OrderbookStorage
) -> None:
    """Upsert currencies touched by the operation. Removed currencies keep their
    row: orders, events and fees reference it."""
    for currency_name, currency_record in storage.currencyLedger.items():
        token = await register_token(
            ctx=ctx,
            address=currency_record.tokenContractAddress,
            token_id=int(currency_record.tokenId),
        )
        currency, _ = await models.OrderbookCurrency.get_or_create(
            orderbook=orderbook, currency_name=currency_name
        )
        currency.token = token
        currency.fa2_token_id = int(currency_record.tokenId)
        currency.decimals = int(currency_record.decimals)
        await currency.save()


async def sync_fee_ledger(
    orderbook: "models.Orderbook", storage: OrderbookStorage
) -> None:
    """Fee ledger keys are the buy currencies plus "rwaToken" (fees taken in the
    traded RWA token)."""
    for currency_name, fee_record in storage.feeLedger.items():
        currency, _ = await models.OrderbookCurrency.get_or_create(
            orderbook=orderbook, currency_name=currency_name
        )
        if currency_name == "rwaToken" and currency.token_id != orderbook.rwa_token_id:
            currency.token_id = orderbook.rwa_token_id
            await currency.save()
        orderbook_fee, _ = await models.OrderbookFee.get_or_create(
            orderbook=orderbook, currency=currency
        )
        orderbook_fee.fee_amount = int(fee_record.nat_0)
        orderbook_fee.paid_fee = int(fee_record.nat_1)
        if currency_name == "rwaToken":
            orderbook_fee.related_token_id = orderbook.rwa_token_id
        await orderbook_fee.save()


async def _sync_price_map(model, rwa_order, price_map: Mapping[str, str]) -> None:
    """Mirror a `counter -> price` map, writing only rows that changed."""
    wanted = {int(counter): int(price) for counter, price in price_map.items()}
    existing = {row.counter: row for row in await model.filter(rwa_order=rwa_order)}
    for counter, row in existing.items():
        if counter not in wanted:
            await row.delete()
        elif row.price != wanted[counter]:
            row.price = wanted[counter]
            await row.save()
    for counter, price in wanted.items():
        if counter not in existing:
            await model.create(rwa_order=rwa_order, counter=counter, price=price)


async def _sync_order_map(model, rwa_order, order_map: Mapping[str, object]) -> None:
    """Mirror a `price -> FIFO bucket` map, writing only rows that changed.
    `order_ids` lists the bucket oldest first, i.e. in match order."""
    wanted = {}
    for price, bucket in order_map.items():
        ordered = sorted(
            (int(counter), int(order_id))
            for counter, order_id in bucket.sortedOrderMap.items()
        )
        wanted[int(price)] = (
            [order_id for _, order_id in ordered],
            int(bucket.headCounter),
            int(bucket.nextCounter),
        )
    existing = {row.price: row for row in await model.filter(rwa_order=rwa_order)}
    for price, row in existing.items():
        if price not in wanted:
            await row.delete()
            continue
        order_ids, head_counter, next_counter = wanted[price]
        if (row.order_ids, row.head_counter, row.next_counter) != wanted[price]:
            row.order_ids = order_ids
            row.head_counter = head_counter
            row.next_counter = next_counter
            await row.save()
    for price, (order_ids, head_counter, next_counter) in wanted.items():
        if price not in existing:
            await model.create(
                rwa_order=rwa_order,
                price=price,
                order_ids=order_ids,
                head_counter=head_counter,
                next_counter=next_counter,
            )


async def sync_book_maps(
    orderbook: "models.Orderbook", storage: OrderbookStorage
) -> None:
    """The price and order maps are plain storage maps, so every operation
    carries them in full; mirror them as-is."""
    rwa_order, _ = await models.OrderbookRwaOrder.get_or_create(
        orderbook=orderbook, rwa_token_id=orderbook.rwa_token_id
    )
    await _sync_price_map(
        models.OrderbookRwaOrderBuyPrice, rwa_order, storage.buyPriceMap
    )
    await _sync_price_map(
        models.OrderbookRwaOrderSellPrice, rwa_order, storage.sellPriceMap
    )
    await _sync_order_map(
        models.OrderbookRwaOrderBuyOrder, rwa_order, storage.buyOrderMap
    )
    await _sync_order_map(
        models.OrderbookRwaOrderSellOrder, rwa_order, storage.sellOrderMap
    )


async def sync_orderbook(
    ctx: HandlerContext, address: str, storage: OrderbookStorage
) -> "models.Orderbook":
    """Mirror everything an order-flow operation can change except the orders
    themselves: config, best prices, counters, currencies, fees and the book."""
    orderbook = await models.Orderbook.get(address=address)
    apply_orderbook_config(orderbook, storage.config)
    apply_orderbook_market_state(orderbook, storage)
    await orderbook.save()
    await sync_currencies(ctx, orderbook, storage)
    await sync_fee_ledger(orderbook, storage)
    await sync_book_maps(orderbook, storage)
    return orderbook


###
# Orders
###


def _utc(value: datetime | None) -> datetime | None:
    """Aware UTC for comparison; a naive value is UTC in this indexer."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _order_state(order: "models.OrderbookOrder") -> tuple[object, ...]:
    """Every column this module writes; unchanged means a no-op write-back."""
    return (
        order.rwa_token_amount,
        order.price_per_rwa_token,
        order.fulfilled_amount,
        order.unfulfilled_amount,
        order.total_paid_out,
        order.total_usd_value_of_rwa_token_amount,
        order.is_fulfilled,
        order.is_canceled,
        order.is_expired,
        order.is_refunded,
        order.refunded_amount,
        order.is_market_order,
        _utc(order.created_at),
        _utc(order.order_expiry),
        _utc(order.ended_at),
        order.operation_hash,
    )


def escrow_held(order_type: "models.OrderType", order: "models.OrderbookOrder") -> int:
    """
    Escrow the contract still holds for an order, mirroring what processRefund
    would return. BUY escrow is in the order's currency, SELL escrow in the RWA
    token.

    - BUY: `totalOrderFulfilled.1 - totalOrderFulfilled.0` until refunded; a
      fully filled buy keeps its price-improvement surplus until processRefund.
    - SELL: until refunded, the fee-net `refundedAmount` a cancel recorded (the
      cancel fee already moved to the fee ledger; the transfer is pending when
      KYC blocked it), otherwise the unfulfilled remainder.
    """
    if order.is_refunded:
        return 0
    if order_type == models.OrderType.BUY:
        return max(0, order.total_usd_value_of_rwa_token_amount - order.total_paid_out)
    if order.refunded_amount > 0:
        return order.refunded_amount
    return order.unfulfilled_amount


async def record_order_event(
    ctx: HandlerContext,
    orderbook: "models.Orderbook",
    order_id: int,
    order_type: "models.OrderType",
    record: OrderLedger,
    intent: "models.OrderEventType",
    data: TezosOperationData,
) -> "models.OrderbookOrder":
    """
    Upsert an OrderbookOrder row from its post-operation ledger record and
    append the OrderbookOrderEvent rows capturing the delta against the
    pre-image.

    `record` is a BuyOrderLedger/SellOrderLedger storage record (the full
    on-chain post-state of the order), `intent` is the event type implied by
    the handler (PLACE/FILL/CANCEL/EXPIRE/REFUND), `data` is the operation's
    TezosOperationData.

    The escrow delta is `escrow_held(after) - escrow_held(before)` and splits
    into what left to the counterparty (fills), back to the initiator
    (`refunded_delta`) and to the fee ledger (`fee_delta`, the cancel fee).
    """
    order = await models.OrderbookOrder.get_or_none(
        orderbook=orderbook, order_type=order_type, order_id=order_id
    )
    created = order is None

    if created:
        currency, _ = await models.OrderbookCurrency.get_or_create(
            orderbook=orderbook, currency_name=record.currency
        )
        user, _ = await models.EquiteezUser.get_or_create(address=record.initiator)
        order = models.OrderbookOrder(
            orderbook=orderbook,
            order_type=order_type,
            order_id=order_id,
            currency=currency,
            initiator=user,
        )
        pre_state = None
        pre_fulfilled = pre_paid_out = 0
        pre_escrow = 0
        pre_flags = (False, False, False, False)
    else:
        pre_state = _order_state(order)
        pre_fulfilled = order.fulfilled_amount
        pre_paid_out = order.total_paid_out
        pre_escrow = escrow_held(order_type, order)
        pre_flags = (
            order.is_fulfilled,
            order.is_canceled,
            order.is_expired,
            order.is_refunded,
        )

    is_fulfilled = record.booleans.bool_0
    is_canceled = record.booleans.bool_1
    is_expired = record.booleans.bool_2
    is_refunded = record.isRefunded

    fulfilled_now = is_fulfilled and not pre_flags[0]
    canceled_now = is_canceled and not pre_flags[1]
    expired_now = is_expired and not pre_flags[2]
    refunded_now = is_refunded and not pre_flags[3]

    order.rwa_token_amount = int(record.rwaTokenAmount)
    order.price_per_rwa_token = int(record.pricePerRwaToken)
    order.fulfilled_amount = int(record.fulfilledAmount)
    order.unfulfilled_amount = int(record.unfulfilledAmount)
    order.total_paid_out = int(record.totalOrderFulfilled.nat_0)
    order.total_usd_value_of_rwa_token_amount = int(record.totalOrderFulfilled.nat_1)
    order.is_fulfilled = is_fulfilled
    order.is_canceled = is_canceled
    order.is_expired = is_expired
    order.is_refunded = is_refunded
    order.refunded_amount = int(record.refundedAmount)
    order.is_market_order = record.isMarketOrder
    order.created_at = parser.parse(record.orderTimestamps.timestamp_0)
    order.order_expiry = (
        parser.parse(record.orderExpiry) if record.orderExpiry else None
    )
    if created or intent == models.OrderEventType.PLACE:
        order.operation_hash = data.hash

    # timestamp_1 is written on fill, cancel, clearExpiredOrders and the
    # closures inside matchOrders, but not when matchOrders flags an order as
    # expired; fall back to the operation time there
    if record.orderTimestamps.timestamp_1:
        order.ended_at = parser.parse(record.orderTimestamps.timestamp_1)
    elif (fulfilled_now or canceled_now or expired_now) and order.ended_at is None:
        order.ended_at = data.timestamp

    fill_delta = order.fulfilled_amount - pre_fulfilled
    spent_delta = order.total_paid_out - pre_paid_out

    # No-op write-back (cancelOrders on a closed order): nothing to store or emit
    if not created and _order_state(order) == pre_state:
        return order

    await order.save()

    escrow_delta = escrow_held(order_type, order) - pre_escrow
    if created:
        refunded_delta = fee_delta = 0
    else:
        refunded_delta = order.refunded_amount if refunded_now else 0
        paid_to_counterparty = (
            fill_delta if order_type == models.OrderType.SELL else spent_delta
        )
        fee_delta = max(0, -escrow_delta - paid_to_counterparty - refunded_delta)

    event_type = intent
    if created and intent != models.OrderEventType.PLACE:
        ctx.logger.warning(
            "Order %s #%s in orderbook %s first seen mid-life via %s op %s; "
            "recording SEED baseline instead of a dated lifecycle event",
            order_type.name,
            order_id,
            orderbook.address,
            intent.name,
            data.hash,
        )
        event_type = models.OrderEventType.SEED
    elif intent == models.OrderEventType.FILL and fill_delta == 0 and spent_delta == 0:
        if canceled_now:
            event_type = models.OrderEventType.CANCEL
        elif expired_now:
            event_type = models.OrderEventType.EXPIRE

    rwa_delta = escrow_delta if order_type == models.OrderType.SELL else 0
    currency_delta = escrow_delta if order_type == models.OrderType.BUY else 0

    events = [
        (
            0,
            event_type,
            rwa_delta,
            currency_delta,
            pre_fulfilled,
            refunded_delta,
            fee_delta,
        )
    ]

    if not created and event_type not in (
        models.OrderEventType.CANCEL,
        models.OrderEventType.EXPIRE,
    ):
        if canceled_now:
            terminal = models.OrderEventType.CANCEL
        elif expired_now:
            terminal = models.OrderEventType.EXPIRE
        else:
            terminal = None
        if terminal is not None:
            events.append((1, terminal, 0, 0, order.fulfilled_amount, 0, 0))

    for seq, evt, rwa, currency, fulfilled_before, refunded, fee in events:
        # get_or_create on the unique_together key — no-op on reorg replay
        await models.OrderbookOrderEvent.get_or_create(
            operation_hash=data.hash,
            counter=data.counter,
            # -1 for top-level, so it cannot collide with an internal op of nonce 0
            batch_index=data.nonce if data.nonce is not None else -1,
            order=order,
            event_seq=seq,
            timestamp=data.timestamp,
            defaults={
                "orderbook": orderbook,
                "initiator_id": order.initiator_id,
                "currency_id": order.currency_id,
                "order_type": order_type,
                "event_type": evt,
                "rwa_delta": rwa,
                "currency_delta": currency,
                "fulfilled_before": fulfilled_before,
                "fulfilled_after": order.fulfilled_amount,
                "unfulfilled_after": order.unfulfilled_amount,
                "refunded_delta": refunded,
                "fee_delta": fee,
                "level": data.level,
            },
        )

    return order


async def record_order_events(
    ctx: HandlerContext,
    orderbook: "models.Orderbook",
    storage: OrderbookStorage,
    intent: "models.OrderEventType | IntentResolver",
    data: TezosOperationData,
) -> None:
    """
    Record every order the operation touched. The order ledgers are big maps,
    so the storage only carries the orders this operation wrote.

    `intent` is either one event type for the whole operation or a callable
    resolving it per (order type, order id), for batches mixing actions.
    """
    ledgers: Iterable[tuple[models.OrderType, Mapping[str, OrderLedger]]] = (
        (models.OrderType.BUY, storage.buyOrderLedger),
        (models.OrderType.SELL, storage.sellOrderLedger),
    )
    for order_type, ledger in ledgers:
        for order_id in ledger:
            await record_order_event(
                ctx,
                orderbook=orderbook,
                order_id=int(order_id),
                order_type=order_type,
                record=ledger[order_id],
                intent=intent(order_type, int(order_id))
                if callable(intent)
                else intent,
                data=data,
            )


###
# Permits
###

_PERMIT_ORDER_INTENTS = {
    "permitCancelOrders": models.OrderEventType.CANCEL,
    "permitProcessRefund": models.OrderEventType.REFUND,
}


async def record_permit_batch(ctx: HandlerContext, transaction) -> None:
    """
    executePermit / permitAndExecute dispatch placeBuyOrder, placeSellOrder,
    cancelOrders and processRefund to the same lambdas as the direct
    entrypoints, with the signer as initiator, so the storage effects match a
    direct call. One batch can mix actions: cancels and refunds name their
    orders explicitly, every other order the batch wrote was just placed.
    """
    intents: dict[tuple[models.OrderType, int], models.OrderEventType] = {}
    for item in transaction.parameter.root:
        name, payload = permit_action(item)
        if name in _PERMIT_ORDER_INTENTS:
            for order in payload:
                key = (models.OrderType[order.orderType], int(order.orderId))
                intents[key] = _PERMIT_ORDER_INTENTS[name]

    orderbook = await sync_orderbook(
        ctx, transaction.data.target_address, transaction.storage
    )
    await record_order_events(
        ctx,
        orderbook=orderbook,
        storage=transaction.storage,
        intent=lambda order_type, order_id: intents.get(
            (order_type, order_id), models.OrderEventType.PLACE
        ),
        data=transaction.data,
    )
