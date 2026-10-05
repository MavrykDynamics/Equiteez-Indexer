import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from dipdup import models as dipdup_models
from dipdup.exceptions import FrameworkException
from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.hooks.on_restart import on_restart
from equiteez.utils.contract_allowlist import QUOTE_TOKENS


ADDRESS = "KT1Token"


class RestartAllowlistTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await Tortoise.init(
            db_url="sqlite://:memory:", modules={"models": ["equiteez.models"]}
        )
        await Tortoise.generate_schemas()
        self.transactions = TransactionManager()
        self.ctx = SimpleNamespace(
            transactions=self.transactions,
            execute_sql=AsyncMock(),
        )
        async with self.transactions.register():
            await models.Token.create(address=ADDRESS)
        self.assert_manager_unregistered()

    async def asyncTearDown(self):
        await Tortoise.close_connections()

    def assert_manager_unregistered(self):
        with self.assertRaisesRegex(
            FrameworkException, "TransactionManager is not registered"
        ):
            dipdup_models.get_transaction()

    async def restart(self, allowlist):
        with patch(
            "equiteez.hooks.update_allowlist_status.fetch_allowlist",
            AsyncMock(return_value=allowlist),
        ):
            await on_restart(self.ctx)
        self.ctx.execute_sql.assert_awaited_once_with("on_restart")

    async def assert_quote_saved(self):
        token = await models.Token.get(address=ADDRESS)
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)

    async def test_schema_init_refresh_saves_without_registered_manager(self):
        await self.restart({QUOTE_TOKENS: {ADDRESS}})
        await self.assert_quote_saved()
        self.assert_manager_unregistered()

    async def test_restart_restores_already_registered_manager(self):
        async with self.transactions.register():
            original_get_transaction = dipdup_models.get_transaction
            original_get_pending_updates = dipdup_models.get_pending_updates
            await self.restart({QUOTE_TOKENS: {ADDRESS}})
            await self.assert_quote_saved()
            self.assertIs(dipdup_models.get_transaction, original_get_transaction)
            self.assertIs(
                dipdup_models.get_pending_updates, original_get_pending_updates
            )
        self.assert_manager_unregistered()

    async def test_failed_fetch_preserves_saved_classification(self):
        async with self.transactions.register():
            token = await models.Token.get(address=ADDRESS)
            token.in_allowlist = True
            token.is_quote_token = True
            await token.save()
        await self.restart(None)
        await self.assert_quote_saved()
        self.assert_manager_unregistered()


if __name__ == "__main__":
    unittest.main()
