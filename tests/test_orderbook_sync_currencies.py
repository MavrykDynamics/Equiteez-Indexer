"""
`sync_currencies` runs on every order-flow operation: it must not hit the
metadata service or rewrite rows unless the currency ledger changed.

    PYTHONPATH=. .venv/bin/python -m unittest tests.test_orderbook_sync_currencies -v
"""

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.types.orderbook.tezos_storage import CurrencyLedger
from equiteez.utils.orderbook_utils import sync_currencies

# 36 characters, the address column width
ORDERBOOK = "KT1" + "TestOrderbook".ljust(33, "0")
USDT = "KT1" + "TestUsdt".ljust(33, "0")


def storage(token_id: str = "0", decimals: str = "6") -> SimpleNamespace:
    return SimpleNamespace(
        currencyLedger={
            "usdt": CurrencyLedger(
                tokenContractAddress=USDT, tokenId=token_id, decimals=decimals
            )
        }
    )


class SyncCurrenciesTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await Tortoise.init(
            db_url="sqlite://:memory:", modules={"models": ["equiteez.models"]}
        )
        try:
            await Tortoise.generate_schemas()
            self._transactions = TransactionManager(depth=None).register()
            await self._transactions.__aenter__()
            self.ctx = SimpleNamespace(logger=logging.getLogger("tests.orderbook"))
            self.orderbook = await models.Orderbook.create(address=ORDERBOOK)
        except BaseException:
            await Tortoise.close_connections()
            raise

    async def asyncTearDown(self) -> None:
        await self._transactions.__aexit__(None, None, None)
        await Tortoise.close_connections()

    async def test_known_token_is_not_re_registered(self) -> None:
        token = await models.Token.create(address=USDT, token_id=0)

        with patch(
            "equiteez.utils.orderbook_utils.register_token", new=AsyncMock()
        ) as register:
            await sync_currencies(self.ctx, self.orderbook, storage())
            register.assert_not_awaited()

        currency = await models.OrderbookCurrency.get(
            orderbook=self.orderbook, currency_name="usdt"
        )
        self.assertEqual(
            (currency.token_id, currency.fa2_token_id, currency.decimals),
            (token.id, 0, 6),
        )

    async def test_unchanged_ledger_writes_nothing(self) -> None:
        await models.Token.create(address=USDT, token_id=0)
        await sync_currencies(self.ctx, self.orderbook, storage())
        before = await models.OrderbookCurrency.get(
            orderbook=self.orderbook, currency_name="usdt"
        )

        with patch.object(models.OrderbookCurrency, "save", new=AsyncMock()) as save:
            await sync_currencies(self.ctx, self.orderbook, storage())
            save.assert_not_awaited()

        after = await models.OrderbookCurrency.get(
            orderbook=self.orderbook, currency_name="usdt"
        )
        self.assertEqual(after.updated_at, before.updated_at)

    async def test_changed_decimals_are_written(self) -> None:
        await models.Token.create(address=USDT, token_id=0)
        await sync_currencies(self.ctx, self.orderbook, storage(decimals="6"))
        await sync_currencies(self.ctx, self.orderbook, storage(decimals="8"))

        currency = await models.OrderbookCurrency.get(
            orderbook=self.orderbook, currency_name="usdt"
        )
        self.assertEqual(currency.decimals, 8)

    async def test_unknown_token_is_registered_once(self) -> None:
        async def fake_register(ctx, address, token_id=0, refresh=False):
            token, _ = await models.Token.get_or_create(
                address=address, token_id=token_id
            )
            return token

        with patch(
            "equiteez.utils.orderbook_utils.register_token",
            new=AsyncMock(side_effect=fake_register),
        ) as register:
            await sync_currencies(self.ctx, self.orderbook, storage(token_id="3"))
            await sync_currencies(self.ctx, self.orderbook, storage(token_id="3"))
            register.assert_awaited_once_with(ctx=self.ctx, address=USDT, token_id=3)

        currency = await models.OrderbookCurrency.get(
            orderbook=self.orderbook, currency_name="usdt"
        )
        await currency.fetch_related("token")
        self.assertEqual((currency.token.address, currency.token.token_id), (USDT, 3))
        self.assertEqual(currency.fa2_token_id, 3)


if __name__ == "__main__":
    unittest.main()
