"""
Table-driven tests for the orderbook escrow / fee / refund delta model in
`equiteez.utils.orderbook_utils.record_order_event`.

Each case feeds the post-operation ledger record of one order (the shape the
contract writes) and checks the OrderbookOrderEvent rows appended against the
pre-image. Runs on in-memory SQLite, outside dipdup:

    PYTHONPATH=. .venv/bin/python -m unittest tests.test_orderbook_order_events -v
"""

import logging
import unittest
from datetime import UTC, datetime, timedelta

from dipdup.models.tezos import TezosOperationData
from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.types.orderbook.tezos_storage import (
    Booleans,
    BuyOrderLedger,
    OrderTimestamps,
    SellOrderLedger,
    TotalOrderFulfilled,
)
from equiteez.utils.orderbook_utils import escrow_held, record_order_event

BUY = models.OrderType.BUY
SELL = models.OrderType.SELL
PLACE = models.OrderEventType.PLACE
FILL = models.OrderEventType.FILL
CANCEL = models.OrderEventType.CANCEL
EXPIRE = models.OrderEventType.EXPIRE
REFUND = models.OrderEventType.REFUND
SEED = models.OrderEventType.SEED

# 36 characters, the address column width
ORDERBOOK = "KT1" + "TestOrderbook".ljust(33, "0")
USER = "mv1" + "TestInitiator".ljust(33, "0")
T0 = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)
T1 = T0 + timedelta(hours=1)


def _chain_ts(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


class _Ctx:
    """Only ctx.logger is used by record_order_event."""

    logger = logging.getLogger("tests.orderbook")


def op(
    hash_: str,
    *,
    level: int = 100,
    counter: int = 1,
    nonce: int | None = None,
) -> TezosOperationData:
    return TezosOperationData(
        type="transaction",
        id=level * 1000 + counter,
        level=level,
        timestamp=T0 + timedelta(minutes=level),
        hash=hash_,
        counter=counter,
        sender_address=USER,
        target_address=ORDERBOOK,
        initiator_address=None,
        amount=0,
        status="applied",
        has_internals=False,
        storage=None,
        nonce=nonce,
    )


def ledger(
    order_type: models.OrderType,
    *,
    amount: int = 100,
    price: int = 10,
    fulfilled: int = 0,
    paid_out: int = 0,
    escrow: int | None = None,
    is_fulfilled: bool = False,
    is_canceled: bool = False,
    is_expired: bool = False,
    is_refunded: bool = False,
    refunded_amount: int = 0,
    ended: datetime | None = None,
    is_market: bool = False,
    currency: str = "usdt",
) -> BuyOrderLedger | SellOrderLedger:
    """
    Post-state of one order as the contract stores it. `paid_out` is
    totalOrderFulfilled.0 (currency paid to the counterparty so far) and
    `escrow` totalOrderFulfilled.1 (the buy escrow deposited at placement,
    amount * price by default).
    """
    cls = BuyOrderLedger if order_type == BUY else SellOrderLedger
    if escrow is None:
        escrow = amount * price if order_type == BUY else 0
    return cls(
        initiator=USER,
        rwaTokenAmount=str(amount),
        pricePerRwaToken=str(price),
        currency=currency,
        fulfilledAmount=str(fulfilled),
        unfulfilledAmount=str(amount - fulfilled),
        totalOrderFulfilled=TotalOrderFulfilled(nat_0=str(paid_out), nat_1=str(escrow)),
        booleans=Booleans(bool_0=is_fulfilled, bool_1=is_canceled, bool_2=is_expired),
        isRefunded=is_refunded,
        refundedAmount=str(refunded_amount),
        orderExpiry=None,
        orderTimestamps=OrderTimestamps(
            timestamp_0=_chain_ts(T0),
            timestamp_1=_chain_ts(ended) if ended else None,
        ),
        isMarketOrder=is_market,
    )


class OrderEventTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await Tortoise.init(
            db_url="sqlite://:memory:", modules={"models": ["equiteez.models"]}
        )
        try:
            await Tortoise.generate_schemas()
            # dipdup models refuse to save outside a registered transaction manager
            self._transactions = TransactionManager(depth=None).register()
            await self._transactions.__aenter__()
            self.ctx = _Ctx()
            self.orderbook = await models.Orderbook.create(address=ORDERBOOK)
        except BaseException:
            # asyncTearDown is skipped when setUp fails, and an open aiosqlite
            # connection keeps the interpreter alive after the failure
            await Tortoise.close_connections()
            raise

    async def asyncTearDown(self) -> None:
        await self._transactions.__aexit__(None, None, None)
        await Tortoise.close_connections()

    async def record(self, order_type, order_id, record, intent, data):
        return await record_order_event(
            self.ctx,
            orderbook=self.orderbook,
            order_id=order_id,
            order_type=order_type,
            record=record,
            intent=intent,
            data=data,
        )

    async def events(self, order) -> list[models.OrderbookOrderEvent]:
        return await models.OrderbookOrderEvent.filter(order=order).order_by(
            "level", "counter", "event_seq"
        )

    def assert_event(
        self,
        event: models.OrderbookOrderEvent,
        event_type: models.OrderEventType,
        *,
        rwa: int = 0,
        currency: int = 0,
        fulfilled_before: int = 0,
        fulfilled_after: int = 0,
        unfulfilled_after: int = 0,
        refunded: int = 0,
        fee: int = 0,
        seq: int = 0,
    ) -> None:
        self.assertEqual(
            (
                event.event_type,
                event.rwa_delta,
                event.currency_delta,
                event.fulfilled_before,
                event.fulfilled_after,
                event.unfulfilled_after,
                event.refunded_delta,
                event.fee_delta,
                event.event_seq,
            ),
            (
                event_type,
                rwa,
                currency,
                fulfilled_before,
                fulfilled_after,
                unfulfilled_after,
                refunded,
                fee,
                seq,
            ),
        )

    # -- placement -----------------------------------------------------------

    async def test_place_buy_escrows_currency(self) -> None:
        order = await self.record(BUY, 1, ledger(BUY), PLACE, op("opA"))

        self.assertEqual(order.operation_hash, "opA")
        self.assertEqual(escrow_held(BUY, order), 1000)
        events = await self.events(order)
        self.assertEqual(len(events), 1)
        self.assert_event(events[0], PLACE, currency=1000, unfulfilled_after=100)
        self.assertEqual(events[0].order_type, BUY)
        self.assertEqual(events[0].batch_index, -1)

    async def test_place_sell_escrows_rwa(self) -> None:
        order = await self.record(SELL, 1, ledger(SELL), PLACE, op("opA"))

        self.assertEqual(escrow_held(SELL, order), 100)
        events = await self.events(order)
        self.assertEqual(len(events), 1)
        self.assert_event(events[0], PLACE, rwa=100, unfulfilled_after=100)

    async def test_internal_operation_keeps_its_nonce_as_batch_index(self) -> None:
        order = await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", nonce=3))
        (event,) = await self.events(order)
        self.assertEqual(event.batch_index, 3)

    # -- fills ---------------------------------------------------------------

    async def test_buy_partial_fill_pays_counterparty_from_escrow(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        order = await self.record(
            BUY,
            1,
            ledger(BUY, fulfilled=40, paid_out=400),
            FILL,
            op("opB", level=101),
        )

        self.assertEqual(escrow_held(BUY, order), 600)
        self.assertIsNone(order.ended_at)
        events = await self.events(order)
        self.assertEqual(len(events), 2)
        self.assert_event(
            events[1],
            FILL,
            currency=-400,
            fulfilled_before=0,
            fulfilled_after=40,
            unfulfilled_after=60,
        )

    async def test_sell_partial_fill_releases_rwa(self) -> None:
        await self.record(SELL, 1, ledger(SELL), PLACE, op("opA", level=100))
        order = await self.record(
            SELL,
            1,
            ledger(SELL, fulfilled=40, paid_out=400),
            FILL,
            op("opB", level=101),
        )

        self.assertEqual(escrow_held(SELL, order), 60)
        events = await self.events(order)
        self.assert_event(
            events[1], FILL, rwa=-40, fulfilled_after=40, unfulfilled_after=60
        )

    async def test_buy_full_fill_keeps_surplus_until_refund(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        # Filled below the limit price: 940 spent of the 1000 escrowed
        order = await self.record(
            BUY,
            1,
            ledger(BUY, fulfilled=100, paid_out=940, is_fulfilled=True, ended=T1),
            FILL,
            op("opB", level=101),
        )

        self.assertTrue(order.is_fulfilled)
        self.assertEqual(order.ended_at, T1)
        self.assertEqual(escrow_held(BUY, order), 60)
        events = await self.events(order)
        self.assertEqual(len(events), 2, "a fill is not a terminal event")
        self.assert_event(
            events[1], FILL, currency=-940, fulfilled_after=100, unfulfilled_after=0
        )

        order = await self.record(
            BUY,
            1,
            ledger(
                BUY,
                fulfilled=100,
                paid_out=940,
                is_fulfilled=True,
                is_refunded=True,
                refunded_amount=60,
                ended=T1,
            ),
            REFUND,
            op("opC", level=102),
        )

        self.assertEqual(escrow_held(BUY, order), 0)
        events = await self.events(order)
        self.assertEqual(len(events), 3)
        self.assert_event(
            events[2],
            REFUND,
            currency=-60,
            refunded=60,
            fulfilled_before=100,
            fulfilled_after=100,
        )

    async def test_fill_that_closes_the_remainder_emits_terminal_cancel(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        # matchOrders fills 95 and cancels the dust remainder, refunding the
        # 50 left in escrow in the same operation
        order = await self.record(
            BUY,
            1,
            ledger(
                BUY,
                fulfilled=95,
                paid_out=950,
                is_canceled=True,
                is_refunded=True,
                refunded_amount=50,
                ended=T1,
            ),
            FILL,
            op("opB", level=101),
        )

        self.assertEqual(escrow_held(BUY, order), 0)
        events = await self.events(order)
        self.assertEqual(len(events), 3)
        self.assert_event(
            events[1],
            FILL,
            currency=-1000,
            refunded=50,
            fulfilled_after=95,
            unfulfilled_after=5,
        )
        self.assert_event(
            events[2],
            CANCEL,
            fulfilled_before=95,
            fulfilled_after=95,
            unfulfilled_after=5,
            seq=1,
        )

    # -- cancels and expiries ------------------------------------------------

    async def test_buy_cancel_refunds_net_of_cancel_fee(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        # cancelOrders on a buy: isRefunded is set, refundedAmount is fee-net
        order = await self.record(
            BUY,
            1,
            ledger(
                BUY, is_canceled=True, is_refunded=True, refunded_amount=990, ended=T1
            ),
            CANCEL,
            op("opB", level=101),
        )

        self.assertEqual(order.ended_at, T1)
        self.assertEqual(escrow_held(BUY, order), 0)
        events = await self.events(order)
        self.assertEqual(len(events), 2, "CANCEL itself is the terminal event")
        self.assert_event(
            events[1],
            CANCEL,
            currency=-1000,
            refunded=990,
            fee=10,
            unfulfilled_after=100,
        )

    async def test_sell_cancel_blocked_by_kyc_then_process_refund(self) -> None:
        await self.record(SELL, 1, ledger(SELL), PLACE, op("opA", level=100))
        # The cancel fee moves to the fee ledger; the transfer back is blocked,
        # so refundedAmount is recorded but isRefunded stays false
        order = await self.record(
            SELL,
            1,
            ledger(SELL, is_canceled=True, refunded_amount=95, ended=T1),
            CANCEL,
            op("opB", level=101),
        )

        self.assertEqual(escrow_held(SELL, order), 95)
        events = await self.events(order)
        self.assertEqual(len(events), 2)
        self.assert_event(events[1], CANCEL, rwa=-5, fee=5, unfulfilled_after=100)

        order = await self.record(
            SELL,
            1,
            ledger(
                SELL, is_canceled=True, is_refunded=True, refunded_amount=95, ended=T1
            ),
            REFUND,
            op("opC", level=102),
        )

        self.assertEqual(escrow_held(SELL, order), 0)
        events = await self.events(order)
        self.assertEqual(len(events), 3)
        self.assert_event(
            events[2], REFUND, rwa=-95, refunded=95, unfulfilled_after=100
        )

    async def test_clear_expired_sell_refunds_and_closes(self) -> None:
        await self.record(SELL, 1, ledger(SELL), PLACE, op("opA", level=100))
        order = await self.record(
            SELL,
            1,
            ledger(
                SELL, is_expired=True, is_refunded=True, refunded_amount=100, ended=T1
            ),
            EXPIRE,
            op("opB", level=101),
        )

        self.assertEqual(order.ended_at, T1)
        self.assertEqual(escrow_held(SELL, order), 0)
        events = await self.events(order)
        self.assertEqual(len(events), 2)
        self.assert_event(
            events[1], EXPIRE, rwa=-100, refunded=100, unfulfilled_after=100
        )

    async def test_match_flagging_expiry_without_close_timestamp(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        # matchOrders marks a stale order expired without writing timestamp_1
        # and without moving funds; the FILL intent must become EXPIRE
        data = op("opB", level=101)
        order = await self.record(BUY, 1, ledger(BUY, is_expired=True), FILL, data)

        self.assertTrue(order.is_expired)
        self.assertEqual(order.ended_at, data.timestamp)
        self.assertEqual(escrow_held(BUY, order), 1000)
        events = await self.events(order)
        self.assertEqual(len(events), 2)
        self.assert_event(events[1], EXPIRE, unfulfilled_after=100)

    # -- idempotency ---------------------------------------------------------

    async def test_noop_write_back_emits_nothing(self) -> None:
        await self.record(BUY, 1, ledger(BUY), PLACE, op("opA", level=100))
        closed = ledger(
            BUY, is_canceled=True, is_refunded=True, refunded_amount=990, ended=T1
        )
        await self.record(BUY, 1, closed, CANCEL, op("opB", level=101))
        # cancelOrders naming an already closed order rewrites it unchanged
        order = await self.record(BUY, 1, closed, CANCEL, op("opC", level=102))

        self.assertEqual(len(await self.events(order)), 2)

    async def test_reorg_replay_is_idempotent(self) -> None:
        data = op("opA", level=100)
        await self.record(BUY, 1, ledger(BUY), PLACE, data)
        order = await self.record(BUY, 1, ledger(BUY), PLACE, data)

        self.assertEqual(len(await self.events(order)), 1)
        self.assertEqual(await models.OrderbookOrder.all().count(), 1)

    async def test_order_first_seen_mid_life_records_seed(self) -> None:
        order = await self.record(
            BUY, 7, ledger(BUY, fulfilled=40, paid_out=400), FILL, op("opA")
        )

        events = await self.events(order)
        self.assertEqual(len(events), 1)
        self.assert_event(
            events[0],
            SEED,
            currency=600,
            fulfilled_after=40,
            unfulfilled_after=60,
        )


if __name__ == "__main__":
    unittest.main()
