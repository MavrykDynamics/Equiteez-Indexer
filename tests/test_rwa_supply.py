"""Run on SQLite by default; RWA_TEST_DATABASE_URL enables PostgreSQL checks.

PostgreSQL tests create and remove a unique schema; they never wipe public data.
The same tests run against the unmodified, locked DipDup dependency in CI.
"""

import copy
import json
import os
import unittest
import uuid
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from dipdup.context import DipDupContext
from dipdup.database import (
    get_tortoise_config,
    set_decimal_precision,
)
from dipdup.index import MatchedHandler
from dipdup.models import Index, IndexStatus, IndexType, ModelUpdate
from dipdup.models.tezos import TezosOperationData
from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.handlers.batch import batch
from equiteez.handlers.on_rwa_storage import on_rwa_storage
from equiteez.hooks.on_index_rollback import on_index_rollback
from equiteez.types.base_token.tezos_storage import BaseTokenStorage
from equiteez.utils.rwa_supply import sync_token_supply

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "KT1Token"
DATABASE = os.environ.get("RWA_TEST_DATABASE_URL")


def diff(path, key, value=None, action="update_key"):
    content = {"key": key}
    if value is not None:
        content["value"] = str(value)
    return {
        "bigmap": 1 if path == "ledger" else 2,
        "path": path,
        "action": action,
        "content": content,
    }


def balance(holder, value=None, token_id="0", action="update_key"):
    return diff("ledger", {"owner": holder, "token_id": token_id}, value, action)


def operation(
    *diffs,
    level=1,
    id=1,
    token_ids=("0",),
    killed=False,
    entrypoint="transfer",
    nonce=None,
    status="applied",
):
    return TezosOperationData.from_json(
        {
            "type": "transaction",
            "id": id,
            "level": level,
            "timestamp": "2026-10-13T00:00:00Z",
            "hash": "opSupply",
            "counter": 1,
            "sender": {"address": "mv1User"},
            "target": {"address": ADDRESS},
            "targetCodeHash": 42,
            "status": status,
            "nonce": nonce,
            "parameter": {"entrypoint": entrypoint, "value": {}},
            "storage": {
                "token_ids": list(token_ids),
                "isKilled": killed,
                "ledger": 1,
                "total_supply": 2,
            },
            "diffs": list(diffs),
        }
    )


class SupplyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Match the native DipDup startup decimal context.
        set_decimal_precision(76)
        config = get_tortoise_config(DATABASE or "sqlite://:memory:", "equiteez")
        self.admin = None
        if DATABASE:
            import asyncpg

            self.schema = "rwa_test_" + uuid.uuid4().hex
            self.admin = await asyncpg.connect(DATABASE)
            await self.admin.execute(f'CREATE SCHEMA "{self.schema}"')
            config["connections"]["default"]["credentials"]["schema"] = self.schema
        await Tortoise.init(config=config)
        await Tortoise.generate_schemas()
        self.db = Tortoise.get_connection("default")
        self.tx = TransactionManager(depth=10)
        self.registration = self.tx.register()
        await self.registration.__aenter__()
        self.state = await Index.create(
            name="rwa_index",
            type=IndexType.tezos_operations,
            status=IndexStatus.realtime,
            level=1,
        )
        self.ctx = DipDupContext(
            config=SimpleNamespace(
                package="equiteez", advanced=SimpleNamespace(rollback_depth=10)
            ),
            package=SimpleNamespace(),
            datasources={},
            transactions=self.tx,
        )
        self.ctx.execute_sql = AsyncMock()
        if DATABASE:
            await self.db.execute_script(
                (
                    ROOT / "equiteez/sql/on_restart/02_create-token-treasury-view.sql"
                ).read_text()
            )
            await self.db.execute_script(
                (
                    ROOT / "equiteez/sql/on_restart/07_create-rwa-supply-view.sql"
                ).read_text()
            )

    async def asyncTearDown(self):
        await self.registration.__aexit__(None, None, None)
        await Tortoise.close_connections()
        if self.admin:
            await self.admin.execute(f'DROP SCHEMA "{self.schema}" CASCADE')
            await self.admin.close()

    async def apply(self, op):
        async with self.tx.in_transaction(level=op.level, index="rwa_index"):
            await sync_token_supply(op)
            await Index.filter(name="rwa_index").update(level=op.level)

    async def amounts(self, token_id="0"):
        token = await models.RwaTokenSupply.get(id=f"{ADDRESS}:{token_id}")
        rows = await models.RwaTokenBalance.filter(token=token)
        return int(token.total_supply_raw), {
            row.holder: int(row.balance_raw) for row in rows
        }

    async def seed(self):
        await self.apply(
            operation(
                diff("total_supply", "0", 1000),
                balance("mv1Treasury", 700),
                balance("mv1User", 300),
            )
        )

    async def launch(self, treasury="mv1Treasury", name="sale", address="KT1Launch"):
        token, _ = await models.Token.get_or_create(address=ADDRESS, token_id=0)
        launchpad, _ = await models.Launchpad.get_or_create(address=address)
        await models.LaunchpadLaunch.create(launchpad=launchpad, token=token, name=name)
        await models.LaunchpadTreasury.get_or_create(
            launchpad=launchpad, name="launchTreasury", defaults={"address": treasury}
        )
        return launchpad

    async def view(self):
        return await self.db.execute_query_dict(
            "SELECT * FROM rwa_supply_view ORDER BY id"
        )

    async def test_default_launchpad_call_updates_treasury(self):
        await self.seed()
        launchpad = await self.launch()
        op = operation(
            diff("treasuryLedger", "launchTreasury", "mv1User"), entrypoint="default"
        )
        op.__dict__["target_address"] = launchpad.address
        op.__dict__["target_code_hash"] = 43
        ctx = SimpleNamespace(
            config=SimpleNamespace(
                contracts={
                    "token_watcher": SimpleNamespace(
                        address=None, resolved_code_hash=42
                    ),
                    "launchpad_watcher": SimpleNamespace(
                        address=None, resolved_code_hash=43
                    ),
                }
            )
        )
        await on_rwa_storage(ctx, op)
        self.assertEqual(
            (await models.LaunchpadTreasury.get(launchpad=launchpad)).address, "mv1User"
        )

    async def test_real_origination_and_first_mint(self):
        for name, kind in (("origination", "origination"), ("mint", "transaction")):
            raw = json.loads((ROOT / f"tests/fixtures/rwa_{name}.json").read_text())
            await self.apply(TezosOperationData.from_json(raw, type_=kind))
        token = await models.RwaTokenSupply.get(
            contract=raw["target"]["address"], token_id="0"
        )
        balances = await models.RwaTokenBalance.filter(token=token)
        self.assertEqual(
            int(token.total_supply_raw), sum(int(row.balance_raw) for row in balances)
        )
        self.assertGreater(token.total_supply_raw, 0)

    async def test_mint_burn_transfer_permit_and_replay(self):
        await self.seed()
        minted = operation(
            diff("total_supply", "0", 1200),
            balance("mv1User", 500),
            level=2,
            entrypoint="mint",
            nonce=0,
        )
        await self.apply(minted)
        await self.apply(minted)
        self.assertEqual(
            await self.amounts(), (1200, {"mv1Treasury": 700, "mv1User": 500})
        )
        await self.apply(
            operation(
                diff("total_supply", "0", 1000),
                balance("mv1User", 300),
                level=3,
                entrypoint="burn",
            )
        )
        await self.apply(
            operation(
                balance("mv1User", 200),
                balance("KT1Orderbook", 100),
                level=4,
                entrypoint="executePermit",
                nonce=1,
            )
        )
        self.assertEqual(
            await self.amounts(),
            (1000, {"mv1Treasury": 700, "mv1User": 200, "KT1Orderbook": 100}),
        )

    async def test_remove_key_and_zero_balance(self):
        await self.seed()
        await self.apply(
            operation(
                balance("mv1User", action="remove_key"),
                balance("mv1Treasury", 0),
                diff("total_supply", "0", action="remove_key"),
                level=2,
            )
        )
        self.assertEqual(await self.amounts(), (0, {}))

    async def test_non_applied_operations_do_not_change_supply(self):
        await self.seed()
        for status in ("failed", "backtracked", "skipped"):
            await self.apply(operation(balance("mv1User", 999), status=status))
        self.assertEqual((await self.amounts())[1]["mv1User"], 300)

    async def test_multiple_token_ids_and_zero_supply(self):
        await self.apply(
            operation(
                diff("total_supply", "99999", 5),
                balance("mv1User", 5, "99999"),
                token_ids=("0", "99999"),
            )
        )
        self.assertEqual(await self.amounts(), (0, {}))
        self.assertEqual(await self.amounts("99999"), (5, {"mv1User": 5}))

    async def test_kill_and_native_rollback_restore_complete_ledger(self):
        await self.seed()
        await self.apply(operation(killed=True, level=2, entrypoint="kill", nonce=0))
        self.assertEqual(await self.amounts(), (0, {}))
        await on_index_rollback(self.ctx, self.state, 2, 1)
        self.assertEqual(
            await self.amounts(), (1000, {"mv1Treasury": 700, "mv1User": 300})
        )
        self.assertEqual((await Index.get(name="rwa_index")).level, 1)
        self.assertFalse(await ModelUpdate.filter(index="rwa_index", level=2).exists())
        await self.apply(
            operation(balance("mv1User", 250), balance("KT1Orderbook", 50), level=2)
        )
        self.assertEqual((await self.amounts())[1]["KT1Orderbook"], 50)

    async def test_rollback_failure_keeps_models_and_index_at_original_level(self):
        await self.seed()
        await self.apply(operation(killed=True, level=2))
        with patch.object(
            Index,
            "filter",
            return_value=SimpleNamespace(
                update=AsyncMock(side_effect=RuntimeError("index write failed"))
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "index write failed"):
                await on_index_rollback(self.ctx, self.state, 2, 1)
        self.assertEqual(await self.amounts(), (0, {}))
        self.assertEqual((await Index.get(name="rwa_index")).level, 2)
        self.assertTrue(await ModelUpdate.filter(index="rwa_index", level=2).exists())

    async def test_batch_orders_mint_before_internal_transfer(self):
        mint = operation(
            diff("total_supply", "0", 100),
            balance("mv1User", 100),
            id=1,
            entrypoint="mint",
        )
        transfer = operation(
            balance("mv1User", 50), balance("KT1Orderbook", 50), id=2, nonce=0
        )
        typed = SimpleNamespace(
            data=transfer, storage=BaseTokenStorage.model_construct()
        )
        handlers = [
            MatchedHandler(
                SimpleNamespace(name="rwa_index"),
                1,
                SimpleNamespace(callback="transfer"),
                (typed,),
            ),
            MatchedHandler(
                SimpleNamespace(name="rwa_index"),
                1,
                SimpleNamespace(callback="on_rwa_storage"),
                (mint,),
            ),
        ]
        ctx = SimpleNamespace(
            config=SimpleNamespace(
                contracts={
                    "token_watcher": SimpleNamespace(
                        address=None, resolved_code_hash=42
                    )
                }
            )
        )

        async def fire(handler):
            if handler.config.callback == "on_rwa_storage":
                await on_rwa_storage(ctx, handler.args[0])

        ctx.fire_matched_handler = fire
        async with self.tx.in_transaction(level=1, index="rwa_index"):
            await batch(ctx, handlers)
        self.assertEqual(
            await self.amounts(), (100, {"mv1User": 50, "KT1Orderbook": 50})
        )

    async def test_real_internal_operation_after_typed_storage_parsing(self):
        from dipdup.indexes.tezos_operations.parser import deserialize_storage

        raw = json.loads(
            (ROOT / "tests/fixtures/rwa_internal_transfer.json").read_text()
        )
        op = TezosOperationData.from_json(copy.deepcopy(raw))
        op, _ = deserialize_storage(op, BaseTokenStorage)
        self.assertIsInstance(op.storage["ledger"], list)
        await self.apply(op)
        for change in raw["diffs"]:
            row = await models.RwaTokenBalance.get(
                token_id=f"{raw['target']['address']}:0",
                holder=change["content"]["key"]["owner"],
            )
            self.assertEqual(int(row.balance_raw), int(change["content"]["value"]))

    async def test_unknown_bigmap_action_aborts_transaction(self):
        await self.seed()
        with self.assertRaisesRegex(ValueError, "Unsupported RWA"):
            await self.apply(
                operation(
                    balance("mv1User", 900), diff("ledger", {}, action="copy"), level=2
                )
            )
        self.assertEqual((await self.amounts())[1]["mv1User"], 300)
        self.assertEqual((await Index.get(name="rwa_index")).level, 1)

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_view_no_launch_and_orderbook_escrow(self):
        await self.seed()
        await self.apply(
            operation(balance("mv1User", 200), balance("KT1Orderbook", 100), level=2)
        )
        (row,) = await self.view()
        self.assertEqual(
            (
                row["total_supply_raw"],
                row["excluded_supply_raw"],
                row["circulating_supply_raw"],
            ),
            (1000, 0, 1000),
        )
        await self.launch()
        (row,) = await self.view()
        self.assertEqual(row["circulating_supply_raw"], 300)

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_shared_treasury_dedup_rotation_and_native_rollback(self):
        await self.seed()
        launchpad = await self.launch()
        await self.launch(name="second")
        await self.launch(name="third", address="KT1OtherLaunch")
        (row,) = await self.view()
        self.assertEqual(row["excluded_supply_raw"], 700)
        async with self.tx.in_transaction(level=2, index="rwa_index"):
            # Remove the other campaign; rotate the first launchpad treasury.
            await models.LaunchpadLaunch.filter(name="third").delete()
            await models.LaunchpadTreasury.filter(launchpad=launchpad).update(
                address="mv1User"
            )
            await Index.filter(name="rwa_index").update(level=2)
        (row,) = await self.view()
        self.assertEqual(
            (row["circulating_supply_raw"], row["indexed_level"]), (700, 2)
        )
        await on_index_rollback(self.ctx, self.state, 2, 1)
        (row,) = await self.view()
        self.assertEqual(
            (row["circulating_supply_raw"], row["indexed_level"]), (300, 1)
        )

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_view_hidden_until_synchronized_and_zero_is_a_value(self):
        await self.apply(operation())
        (row,) = await self.view()
        self.assertEqual(row["circulating_supply_raw"], 0)
        await Index.filter(name="rwa_index").update(status=IndexStatus.syncing)
        self.assertEqual(await self.view(), [])

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_precision_exceeds_javascript_and_decimal_default_context(self):
        amount = 10**60 + 123456789
        await self.apply(
            operation(
                diff("total_supply", "0", amount),
                balance("mv1Treasury", amount - 17),
                balance("mv1User", 17),
            )
        )
        await self.launch()
        (row,) = await self.view()
        self.assertEqual(row["total_supply_raw"], Decimal(amount))
        self.assertEqual(row["circulating_supply_raw"], 17)

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_incomplete_ledger_is_not_published(self):
        await self.seed()
        await self.apply(operation(balance("mv1User", 1)))
        self.assertEqual(await self.view(), [])

    @unittest.skipUnless(DATABASE, "Requires PostgreSQL")
    async def test_old_index_requires_reindex_and_fresh_sql_is_repeatable(self):
        sql = (
            ROOT / "equiteez/sql/on_restart/07_create-rwa-supply-view.sql"
        ).read_text()
        await self.db.execute_script(sql)
        await Index.create(
            name="token_index", type=IndexType.tezos_operations, level=50
        )
        with self.assertRaisesRegex(Exception, "full DipDup schema reindex"):
            await self.db.execute_script(sql)


if __name__ == "__main__":
    unittest.main()
