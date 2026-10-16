"""Purchase payment attribution and immutable event snapshots."""

import copy
import json
import logging
import unittest
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

from dipdup.indexes.tezos_operations.parser import deserialize_storage
from dipdup.models import ModelUpdate
from dipdup.models.tezos import TezosOperationData
from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.handlers.launchpad.purchase import purchase as handle_purchase
from equiteez.models.natural import NaturalField
from equiteez.types.launchpad.tezos_parameters.purchase import PurchaseParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils import launchpad_purchase_payments as payments
from equiteez.utils.launchpad_purchase_payments import PurchaseTerms, payment_totals
from equiteez.utils.launchpad_utils import apply_purchase, record_permit_batch


LP, BUYER, TOKEN, RWA = "KT1Launchpad", "mv1Buyer", "KT1Payment", "KT1Rwa"
TREASURY = {
    "assetTreasury": "mv1Asset",
    "feeTreasury": "mv1Fee",
    "launchTreasury": "mv1Inventory",
}
T0 = datetime(2026, 10, 16, tzinfo=UTC)


def operation():
    return NS(
        id=100,
        hash="op-purchase",
        counter=17,
        nonce=None,
        level=1000,
        block="block",
        target_address=LP,
        sender_address=BUYER,
        amount=0,
        entrypoint="purchase",
    )


def terms(**kwargs):
    base = PurchaseTerms(
        BUYER,
        1000000,
        100000000,
        100000000,
        200,
        "fa2",
        TOKEN,
        7,
        "MANUAL",
        "MINT",
        RWA,
        0,
    )
    return replace(base, **kwargs)


def parent(data):
    return {
        "id": data.id,
        "hash": data.hash,
        "counter": data.counter,
        "nonce": data.nonce,
        "level": data.level,
        "block": data.block,
        "status": "applied",
        "target": {"address": data.target_address},
        "sender": {"address": data.sender_address},
    }


def transfer(term, recipient, amount):
    if term.currency == "mav":
        return {"target": {"address": recipient}, "amount": amount, "parameter": None}
    value = (
        {"from": term.buyer, "to": recipient, "value": str(amount)}
        if term.currency == "fa12"
        else [
            {
                "from_": term.buyer,
                "txs": [
                    {
                        "to_": recipient,
                        "token_id": str(term.token_id),
                        "amount": str(amount),
                    }
                ],
            }
        ]
    )
    return {
        "target": {"address": term.token_address},
        "amount": 0,
        "parameter": {"entrypoint": "transfer", "value": value},
    }


def receipt(data, term_list, discounts, treasury=TREASURY):
    result = [parent(data)]
    expected = []
    for term, discount in zip(term_list, discounts, strict=True):
        subtotal = (term.price * term.amount + 999999) // 1000000
        net = subtotal - subtotal * term.fee_bps // 10000
        fee = subtotal * term.fee_bps * (10000 - discount) // 100000000
        group = []
        if term.distribution == "AUTO":
            if term.issuance == "MINT":
                group.append(
                    {
                        "target": {"address": term.rwa_address},
                        "amount": 0,
                        "parameter": {
                            "entrypoint": "mint",
                            "value": [
                                {
                                    "owner": term.buyer,
                                    "token_id": str(term.rwa_id),
                                    "amount": str(term.amount),
                                }
                            ],
                        },
                    }
                )
            else:
                issuance = replace(
                    term,
                    currency="fa2",
                    token_address=term.rwa_address,
                    token_id=term.rwa_id,
                    buyer=treasury["launchTreasury"],
                )
                group.append(transfer(issuance, term.buyer, term.amount))
        group.append(transfer(term, treasury["assetTreasury"], net))
        if fee:
            group.append(transfer(term, treasury["feeTreasury"], fee))
        for op in group:
            # Intentionally descending nonces, ascending execution IDs.
            result.append(
                {
                    **parent(data),
                    **op,
                    "sender": {"address": LP},
                    "id": data.id + len(result),
                    "nonce": 10000 - len(result),
                }
            )
        expected.append(net + fee)
    return result, tuple(expected)


class PaymentAttributionTests(unittest.TestCase):
    def test_currencies_discounts_rounding_and_zero(self):
        for currency in ("fa2", "fa12", "mav"):
            for discount in (0, 5000, 10000):
                for mode in ("AUTO", "MANUAL"):
                    for amount, price, bps in (
                        (1000000, 100000000, 200),
                        (1, 3, 200),
                        (1700000, 9, 0),
                        (1000000, 0, 0),
                        (1000000, 2**100, 200),
                    ):
                        with self.subTest(
                            currency=currency,
                            discount=discount,
                            mode=mode,
                            amount=amount,
                            price=price,
                            bps=bps,
                        ):
                            t = terms(
                                currency=currency,
                                distribution=mode,
                                amount=amount,
                                price=price,
                                maximum=2**150,
                                fee_bps=bps,
                            )
                            data = operation()
                            rows, want = receipt(data, [t], [discount])
                            if currency == "mav":
                                data.amount = want[0]
                            self.assertEqual(
                                payment_totals(data, rows, [t], TREASURY), (want, None)
                            )

    def test_batch_shared_buyer_currency_and_treasuries(self):
        data = operation()
        data.entrypoint = "executePermit"
        treasury = {**TREASURY, "feeTreasury": TREASURY["assetTreasury"]}
        terms_list = [
            terms(),
            terms(
                amount=2000000,
                maximum=300000000,
                distribution="AUTO",
                issuance="TRANSFER",
            ),
            terms(price=0),
        ]
        rows, want = receipt(data, terms_list, [0, 5000, 10000], treasury)
        self.assertEqual(payment_totals(data, rows, terms_list, treasury), (want, None))
        # Sibling content in the same operation group is not part of this call.
        unrelated = copy.deepcopy(rows[-1])
        unrelated["counter"] += 1
        unrelated["id"] += 1
        self.assertEqual(
            payment_totals(data, [*rows, unrelated], terms_list, treasury), (want, None)
        )

    def test_rejects_wrong_asset_buyer_extra_operations_and_nested_calls(self):
        data = operation()
        term = terms()
        base, _ = receipt(data, [term], [0])
        for mutation in (
            "token_id",
            "sender",
            "target",
            "extra",
            "nested",
            "missing",
            "failed",
            "duplicate",
            "wrong_net",
        ):
            rows = copy.deepcopy(base)
            if mutation == "token_id":
                rows[1]["parameter"]["value"][0]["txs"][0]["token_id"] = "0"
            elif mutation == "sender":
                rows[1]["parameter"]["value"][0]["from_"] = "mv1Other"
            elif mutation == "target":
                rows[1]["target"]["address"] = "KT1Other"
            elif mutation == "wrong_net":
                rows[1]["parameter"]["value"][0]["txs"][0]["amount"] = "123"
            elif mutation == "extra":
                extra = copy.deepcopy(rows[-1])
                extra["id"] += 1
                extra["nonce"] -= 1
                rows.append(extra)
            elif mutation == "nested":
                extra = parent(data)
                extra["id"] += 100
                extra["nonce"] = 99
                rows.append(extra)
            elif mutation == "missing":
                rows = rows[:1]
            elif mutation == "duplicate":
                rows.append(copy.deepcopy(rows[-1]))
            elif mutation == "failed":
                rows[1]["status"] = "failed"
            with self.subTest(mutation=mutation):
                if mutation == "failed":
                    with self.assertRaises(RuntimeError):
                        payment_totals(data, rows, [term], TREASURY)
                else:
                    total, reason = payment_totals(data, rows, [term], TREASURY)
                    self.assertIsNone(total)
                    self.assertIsNotNone(reason)

    def test_ambiguous_batch_is_not_guessed(self):
        data = operation()
        data.entrypoint = "executePermit"
        t = terms(price=2, fee_bps=5000)
        treasury = {**TREASURY, "feeTreasury": TREASURY["assetTreasury"]}
        rows, _ = receipt(data, [t, t], [0, 10000], treasury)
        total, reason = payment_totals(data, rows, [t, t], treasury)
        self.assertIsNone(total)
        self.assertEqual(reason, "ambiguous_or_unmatched_payments")

    def test_missing_parent_and_wrong_block_are_retryable(self):
        data = operation()
        rows, _ = receipt(data, [terms()], [0])
        with self.assertRaises(RuntimeError):
            payment_totals(data, [], [terms()], TREASURY)
        rows[0]["block"] = "reorg"
        with self.assertRaises(RuntimeError):
            payment_totals(data, rows, [terms()], TREASURY)

    def test_maximum_is_never_used_as_total(self):
        data = operation()
        t = terms(maximum=999999999)
        rows, want = receipt(data, [t], [5000])
        self.assertEqual(payment_totals(data, rows, [t], TREASURY), (want, None))
        self.assertNotEqual(want[0], t.maximum)

    def test_natural_field_is_exact_and_rejects_invalid_values(self):
        field = NaturalField(null=True)
        self.assertEqual(field.to_python_value(str(2**256)), 2**256)
        self.assertEqual(field.to_db_value(2**256, None), 2**256)
        self.assertIsNone(field.to_python_value(None))
        for value in (-1, "1.5", "NaN", "Infinity", 1.0, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                field.to_python_value(value)


class PurchaseSnapshotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        payments._last_receipt = None
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["dipdup.models", "equiteez.models"]},
        )
        await Tortoise.generate_schemas()
        self.manager = TransactionManager(depth=5)
        self.transactions = self.manager.register()
        await self.transactions.__aenter__()
        self.raw = json.loads(
            (
                Path(__file__).parent / "fixtures/launchpad_purchase_receipt.json"
            ).read_text()
        )
        raw = copy.deepcopy(self.raw[0])
        data = TezosOperationData.from_json(raw)
        data, storage = deserialize_storage(data, LaunchpadStorage)
        self.transaction = NS(
            data=data,
            storage=storage,
            parameter=PurchaseParameter.model_validate(data.parameter_json),
        )
        self.datasource = NS(request=AsyncMock(return_value=self.raw))
        self.ctx = NS(
            logger=logging.getLogger("tests.purchase"),
            handler_config=NS(parent=NS(datasources=[NS(name="mvkt")])),
            get_tezos_tzkt_datasource=lambda name: self.datasource,
        )
        self.launchpad = await models.Launchpad.create(address=data.target_address)
        self.launch = await models.LaunchpadLaunch.create(
            launchpad=self.launchpad, name=self.transaction.parameter.launchName
        )
        self.option = await models.LaunchpadSaleOption.create(
            launch=self.launch, name=self.transaction.parameter.saleOption
        )
        launch = storage.launchLedger[self.launch.name]
        payment = launch.saleOptions[self.option.name].payments[
            self.transaction.parameter.payment
        ]
        await models.Token.create(
            address=payment.currency.fa2.tokenContractAddress,
            token_id=int(payment.currency.fa2.tokenId),
        )
        recipient = self.raw[2]["parameter"]["value"][0]["txs"][0]["to_"]
        for name in ("assetTreasury", "feeTreasury", "launchTreasury"):
            await models.LaunchpadTreasury.create(
                launchpad=self.launchpad, name=name, address=recipient
            )

    async def asyncTearDown(self):
        await self.transactions.__aexit__(None, None, None)
        await Tortoise.close_connections()
        payments._last_receipt = None

    async def test_real_receipt_handler_and_replay_preserve_snapshots(self):
        await handle_purchase(self.ctx, self.transaction)
        row = await models.LaunchpadPurchaseEvent.get()
        self.assertEqual(
            (row.price, row.total, row.token_distribution_type),
            (30000000, 41100000, models.TokenDistributionType.AUTO),
        )
        self.assertEqual(row.operation_counter, self.transaction.data.counter)
        self.assertEqual(row.operation_nonce, -1)
        self.assertEqual(row.amount, 1370000)
        # Changing indexed settings cannot affect the existing event.
        self.transaction.storage.launchLedger[
            self.launch.name
        ].tokenDistributionType = "MANUAL"
        await handle_purchase(self.ctx, self.transaction)
        replay = await models.LaunchpadPurchaseEvent.get()
        self.assertEqual(
            (replay.id, replay.price, replay.total, replay.token_distribution_type),
            (row.id, row.price, row.total, row.token_distribution_type),
        )
        self.datasource.request.assert_awaited_once()

    async def test_snapshot_large_values_admin_unknown_and_call_identity(self):
        storage = self.transaction.storage
        params = self.transaction.parameter
        launch = storage.launchLedger[self.launch.name]
        option = launch.saleOptions[self.option.name]
        option.payments[params.payment].price = str(2**200)
        record = storage.purchaseLedger[0].value
        kwargs = dict(
            ctx=self.ctx,
            launchpad=self.launchpad,
            launch_name=self.launch.name,
            user_address=self.transaction.data.sender_address,
            sale_option_name=self.option.name,
            payment_name=params.payment,
            event_amount=1,
            operation_hash="op-test",
            timestamp=T0,
            level=1,
            source=models.PurchaseSource.USER,
            launch_record=launch,
            sale_option_record=option,
            purchase_record=record,
            total=2**201,
        )
        await apply_purchase(**kwargs, operation_counter=7)
        await apply_purchase(**kwargs, operation_counter=8)
        await apply_purchase(**kwargs, operation_counter=8, operation_nonce=0)
        self.assertEqual(await models.LaunchpadPurchaseEvent.all().count(), 3)
        row = await models.LaunchpadPurchaseEvent.get(operation_counter=7)
        self.assertEqual((row.price, row.total), (2**200, 2**201))
        await apply_purchase(
            **{**kwargs, "source": models.PurchaseSource.ADMIN}, operation_counter=9
        )
        admin = await models.LaunchpadPurchaseEvent.get(operation_counter=9)
        self.assertIsNone(admin.price)
        self.assertIsNone(admin.total)
        launch.tokenDistributionType = "FUTURE"
        await apply_purchase(**kwargs, operation_counter=10)
        self.assertIsNone(
            (
                await models.LaunchpadPurchaseEvent.get(operation_counter=10)
            ).token_distribution_type
        )

    async def test_large_snapshot_delete_and_rollback_are_exact(self):
        await handle_purchase(self.ctx, self.transaction)
        row = await models.LaunchpadPurchaseEvent.get()
        row.price, row.total = 2**256, 2**257
        await row.save()
        row = await models.LaunchpadPurchaseEvent.get(id=row.id)
        async with self.manager.in_transaction(level=101, index="launchpad"):
            await row.delete()
        update = await ModelUpdate.get(level=101, model_name="LaunchpadPurchaseEvent")
        self.assertEqual(update.data["price"], str(2**256))
        await update.revert(models.LaunchpadPurchaseEvent)
        restored = await models.LaunchpadPurchaseEvent.get(id=row.id)
        self.assertEqual((restored.price, restored.total), (2**256, 2**257))

    async def test_legacy_row_is_not_replaced_or_duplicated(self):
        data = self.transaction.data
        user = await models.EquiteezUser.create(address=data.sender_address)
        row = await models.LaunchpadPurchaseEvent.create(
            launch=self.launch,
            user=user,
            sale_option=self.option,
            payment_name="USDT",
            amount=1370000,
            source=models.PurchaseSource.USER,
            operation_hash=data.hash,
            timestamp=data.timestamp,
            level=data.level,
        )
        await handle_purchase(self.ctx, self.transaction)
        after = await models.LaunchpadPurchaseEvent.get()
        self.assertEqual(row.id, after.id)
        self.assertIsNone(after.price)
        self.assertIsNone(after.total)

    async def test_receipt_network_failure_does_not_append_event(self):
        self.datasource.request.side_effect = TimeoutError("receipt unavailable")
        with self.assertRaises(TimeoutError):
            await handle_purchase(self.ctx, self.transaction)
        self.assertEqual(await models.LaunchpadPurchaseEvent.all().count(), 0)

    async def test_historical_projection_without_block_hash_is_verified(self):
        self.transaction.data = replace(self.transaction.data, block=None)
        stale = copy.deepcopy(self.raw)
        stale[0]["diffs"][0]["content"]["value"]["purchaseFeePercent"] = "999"
        self.datasource.request.side_effect = [stale, self.raw]
        with self.assertRaises(RuntimeError):
            await handle_purchase(self.ctx, self.transaction)
        self.assertEqual(await models.LaunchpadPurchaseEvent.all().count(), 0)
        await handle_purchase(self.ctx, self.transaction)
        self.assertEqual((await models.LaunchpadPurchaseEvent.get()).total, 41100000)
        self.assertIsNone(payments._last_receipt)

    async def test_stale_receipt_does_not_poison_the_block_cache(self):
        stale = copy.deepcopy(self.raw)
        stale[0]["block"] = "old-fork"
        self.datasource.request.side_effect = [stale, self.raw]
        with self.assertRaises(RuntimeError):
            await handle_purchase(self.ctx, self.transaction)
        self.assertEqual(await models.LaunchpadPurchaseEvent.all().count(), 0)
        await handle_purchase(self.ctx, self.transaction)
        self.assertEqual((await models.LaunchpadPurchaseEvent.get()).total, 41100000)
        self.assertEqual(self.datasource.request.await_count, 2)

    async def test_permit_batch_uses_signer_and_per_purchase_totals(self):
        tx = self.transaction
        buyer = tx.data.sender_address
        item = NS(
            signer=buyer,
            action=NS(
                permitPurchase=tx.parameter,
                model_dump=lambda **kw: {"permitPurchase": {}},
            ),
        )
        # Two identical purchases in one permit call, with separate effect groups.
        tx.parameter = NS(root=[item, item])
        tx.data = replace(
            tx.data, entrypoint="executePermit", sender_address="mv1Sponsor"
        )
        rows = copy.deepcopy(self.raw)
        rows[0]["sender"]["address"] = "mv1Sponsor"
        for op in self.raw[1:]:
            extra = copy.deepcopy(op)
            extra["id"] += 10000000
            extra["nonce"] += 3
            rows.append(extra)
        self.datasource.request.return_value = rows
        await record_permit_batch(self.ctx, tx)
        events = await models.LaunchpadPurchaseEvent.all().order_by("batch_index")
        self.assertEqual([r.batch_index for r in events], [0, 1])
        self.assertEqual([r.total for r in events], [41100000, 41100000])
        for row in events:
            await row.fetch_related("user")
            self.assertEqual(row.user.address, buyer)
        self.datasource.request.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
