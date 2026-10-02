import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from equiteez.handlers.tokens.origination import origination
from equiteez.handlers.transfers.on_transfer import on_transfer
from equiteez.hooks.update_allowlist_status import update_allowlist_status
from equiteez.utils.contract_allowlist import (
    BASE_TOKENS,
    QUOTE_TOKENS,
    token_in_allowlist,
)


ADDRESS = "KT1Token"


def make_token(*, token_id=0, in_allowlist=False, is_quote_token=False):
    return SimpleNamespace(
        address=ADDRESS,
        token_id=token_id,
        in_allowlist=in_allowlist,
        is_quote_token=is_quote_token,
        metadata=None,
        token_metadata=None,
        token_standard=None,
        save=AsyncMock(),
    )


class TokenAllowlistTests(unittest.TestCase):
    def test_membership_in_either_token_list(self):
        cases = (
            (None, False),
            ({}, False),
            ({BASE_TOKENS: set(), QUOTE_TOKENS: set()}, False),
            ({BASE_TOKENS: {ADDRESS}}, True),
            ({QUOTE_TOKENS: {ADDRESS}}, True),
            ({BASE_TOKENS: {ADDRESS}, QUOTE_TOKENS: {ADDRESS}}, True),
            ({BASE_TOKENS: {"other"}, QUOTE_TOKENS: {"other"}}, False),
        )
        for allowlist, expected in cases:
            with self.subTest(allowlist=allowlist):
                self.assertEqual(token_in_allowlist(allowlist, ADDRESS), expected)


class TokenAllowlistRefreshTests(unittest.IsolatedAsyncioTestCase):
    async def refresh(self, tokens, allowlist):
        module = "equiteez.hooks.update_allowlist_status"
        with ExitStack() as patches:
            patches.enter_context(
                patch(f"{module}.fetch_allowlist", AsyncMock(return_value=allowlist))
            )
            patches.enter_context(
                patch(f"{module}.models.Token.all", AsyncMock(return_value=tokens))
            )
            for model in ("Orderbook", "SuperAdmin", "Kyc", "Launchpad"):
                patches.enter_context(
                    patch(f"{module}.models.{model}.all", AsyncMock(return_value=[]))
                )
            await update_allowlist_status(SimpleNamespace())

    async def test_base_to_quote_reclassifies_without_changing_membership(self):
        tokens = [
            make_token(in_allowlist=True),
            make_token(token_id=7, in_allowlist=True),
        ]
        await self.refresh(tokens, {QUOTE_TOKENS: {ADDRESS}})
        for token in tokens:
            self.assertTrue(token.in_allowlist)
            self.assertTrue(token.is_quote_token)
            token.save.assert_awaited_once()

    async def test_quote_to_base_clears_quote_flag(self):
        token = make_token(in_allowlist=True, is_quote_token=True)
        await self.refresh([token], {BASE_TOKENS: {ADDRESS}})
        self.assertTrue(token.in_allowlist)
        self.assertFalse(token.is_quote_token)
        token.save.assert_awaited_once()

    async def test_removed_token_clears_both_flags(self):
        token = make_token(in_allowlist=True, is_quote_token=True)
        await self.refresh([token], {})
        self.assertFalse(token.in_allowlist)
        self.assertFalse(token.is_quote_token)
        token.save.assert_awaited_once()

    async def test_token_in_both_lists_is_identified_as_quote(self):
        token = make_token()
        await self.refresh([token], {BASE_TOKENS: {ADDRESS}, QUOTE_TOKENS: {ADDRESS}})
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)

    async def test_fetch_failure_preserves_both_flags(self):
        token = make_token(in_allowlist=True, is_quote_token=True)
        await self.refresh([token], None)
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)
        token.save.assert_not_awaited()

    async def test_unchanged_token_is_not_saved(self):
        token = make_token(in_allowlist=True, is_quote_token=True)
        await self.refresh([token], {QUOTE_TOKENS: {ADDRESS}})
        token.save.assert_not_awaited()


class TokenOriginationAllowlistTests(unittest.IsolatedAsyncioTestCase):
    async def originate(self, token, allowlist):
        module = "equiteez.handlers.tokens.origination"
        with (
            patch(f"{module}.register_token", AsyncMock(return_value=token)),
            patch(f"{module}.fetch_allowlist", AsyncMock(return_value=allowlist)),
            patch(f"{module}.models.Token.get_or_none", AsyncMock(return_value=token)),
        ):
            await origination(
                SimpleNamespace(),
                SimpleNamespace(
                    data=SimpleNamespace(originated_contract_address=ADDRESS, level=1)
                ),
            )

    async def test_originated_quote_token_has_both_flags(self):
        token = make_token()
        await self.originate(token, {QUOTE_TOKENS: {ADDRESS}})
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)
        token.save.assert_awaited_once()

    async def test_originated_base_token_is_not_a_quote(self):
        token = make_token()
        await self.originate(token, {BASE_TOKENS: {ADDRESS}})
        self.assertTrue(token.in_allowlist)
        self.assertFalse(token.is_quote_token)

    async def test_fetch_failure_preserves_existing_flags(self):
        token = make_token(in_allowlist=True, is_quote_token=True)
        await self.originate(token, None)
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)
        token.save.assert_not_awaited()


class TransferAllowlistTests(unittest.IsolatedAsyncioTestCase):
    async def test_new_token_id_inherits_quote_classification(self):
        base_token = make_token(in_allowlist=True, is_quote_token=True)
        token = make_token(token_id=7)
        transfer = SimpleNamespace(
            data=SimpleNamespace(
                nonce=None,
                level=1,
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                target_address=ADDRESS,
                hash="operation",
            ),
            parameter=SimpleNamespace(
                root=[
                    SimpleNamespace(
                        from_="mv1Sender",
                        txs=[SimpleNamespace(to_="mv1Receiver", token_id=7, amount=1)],
                    )
                ]
            ),
        )
        module = "equiteez.handlers.transfers.on_transfer"
        with (
            patch(f"{module}.models.Token.get_or_none", AsyncMock(return_value=None)),
            patch(f"{module}.register_token", AsyncMock(return_value=base_token)),
            patch(
                f"{module}.models.Token.get_or_create",
                AsyncMock(return_value=(token, True)),
            ),
            patch(f"{module}.get_contract_token_metadata", AsyncMock(return_value={})),
            patch(
                f"{module}.models.EquiteezUser.get_or_create",
                AsyncMock(return_value=(SimpleNamespace(), True)),
            ),
            patch(
                f"{module}.models.EquiteezUserTokenTransfer",
                return_value=SimpleNamespace(save=AsyncMock()),
            ),
        ):
            await on_transfer(SimpleNamespace(), transfer)
        self.assertTrue(token.in_allowlist)
        self.assertTrue(token.is_quote_token)
        token.save.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
