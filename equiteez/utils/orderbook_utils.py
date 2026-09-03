from collections.abc import Iterable, Mapping
from datetime import UTC, datetime

from dateutil import parser
from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOperationData

from equiteez import models as models
from equiteez.types.orderbook.tezos_storage import BuyOrderLedger, SellOrderLedger

OrderLedger = BuyOrderLedger | SellOrderLedger


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
        pre_fulfilled = pre_paid_out = pre_refunded = 0
        pre_flags = (False, False, False, False)
    else:
        pre_state = _order_state(order)
        pre_fulfilled = order.fulfilled_amount
        pre_paid_out = order.total_paid_out
        pre_refunded = order.refunded_amount
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

    if record.orderTimestamps.timestamp_1:
        order.ended_at = parser.parse(record.orderTimestamps.timestamp_1)
    elif (fulfilled_now or canceled_now or expired_now) and order.ended_at is None:
        order.ended_at = data.timestamp

    fill_delta = order.fulfilled_amount - pre_fulfilled
    spent_delta = order.total_paid_out - pre_paid_out
    refunded_delta = order.refunded_amount - pre_refunded

    # No-op write-back (cancelOrders on a closed order): nothing to store or emit
    if not created and _order_state(order) == pre_state:
        return order

    await order.save()

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

    rwa_delta = 0
    currency_delta = 0
    if order_type == models.OrderType.SELL:
        if created:
            rwa_delta += order.rwa_token_amount
        rwa_delta -= fill_delta + refunded_delta
    else:
        if created:
            currency_delta += order.total_usd_value_of_rwa_token_amount
        currency_delta -= spent_delta + refunded_delta

    events = [(0, event_type, rwa_delta, currency_delta, pre_fulfilled, refunded_delta)]

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
            events.append((1, terminal, 0, 0, order.fulfilled_amount, 0))

    for seq, evt, rwa, currency, fulfilled_before, refunded in events:
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
                "level": data.level,
            },
        )

    return order


async def record_order_events(
    ctx: HandlerContext,
    orderbook: "models.Orderbook",
    ledgers: Iterable[tuple["models.OrderType", Mapping[str, OrderLedger]]],
    intent: "models.OrderEventType",
    data: TezosOperationData,
) -> None:
    for order_type, ledger in ledgers:
        for order_id in ledger:
            await record_order_event(
                ctx,
                orderbook=orderbook,
                order_id=int(order_id),
                order_type=order_type,
                record=ledger[order_id],
                intent=intent,
                data=data,
            )
