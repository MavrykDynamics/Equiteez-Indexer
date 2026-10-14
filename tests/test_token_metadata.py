import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.handlers.tokens.kill import kill
from equiteez.hooks.update_allowlist_status import update_allowlist_status
from equiteez.models.shared import TokenType
from equiteez.utils.contract_allowlist import QUOTE_TOKENS
from equiteez.utils.utils import register_token


ADDRESS = "KT1" + "MetadataToken".ljust(33, "0")
OLD_TIME = datetime(2000, 1, 1, tzinfo=timezone.utc)


class TokenMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await Tortoise.init(
            db_url="sqlite://:memory:", modules={"models": ["equiteez.models"]}
        )
        await Tortoise.generate_schemas()
        self.transactions = TransactionManager().register()
        await self.transactions.__aenter__()
        self.ctx = SimpleNamespace()
        self.token = await models.Token.create(
            address=ADDRESS,
            token_id=7,
            metadata={"name": "Contract"},
            token_metadata={"symbol": "OLD"},
            token_standard=TokenType.FA2,
        )
        await models.Token.filter(id=self.token.id).update(updated_at=OLD_TIME)

    async def asyncTearDown(self):
        await self.transactions.__aexit__(None, None, None)
        await Tortoise.close_connections()

    async def refresh(self, metadata, token_metadata, **kwargs):
        with (
            patch(
                "equiteez.utils.utils.get_contract_metadata",
                AsyncMock(return_value=metadata),
            ),
            patch(
                "equiteez.utils.utils.get_contract_token_metadata",
                AsyncMock(return_value=token_metadata),
            ) as fetch_token_metadata,
        ):
            result = await register_token(self.ctx, ADDRESS, token_id=7, **kwargs)
        return result, fetch_token_metadata

    async def test_refresh_does_not_overwrite_interleaved_kill_and_allowlist(self):
        async def fetch_metadata(**kwargs):
            await kill(
                self.ctx,
                SimpleNamespace(
                    data=SimpleNamespace(target_address=ADDRESS),
                    storage=SimpleNamespace(isKilled=True),
                ),
            )
            with patch(
                "equiteez.hooks.update_allowlist_status.fetch_allowlist",
                AsyncMock(return_value={QUOTE_TOKENS: {ADDRESS}}),
            ):
                await update_allowlist_status(self.ctx)
            return {"name": "Updated contract"}

        with (
            patch("equiteez.utils.utils.get_contract_metadata", fetch_metadata),
            patch(
                "equiteez.utils.utils.get_contract_token_metadata",
                AsyncMock(return_value={"symbol": "NEW"}),
            ) as fetch_token_metadata,
        ):
            await register_token(self.ctx, ADDRESS, token_id=7, refresh=True)

        saved = await models.Token.get(id=self.token.id)
        self.assertTrue(saved.is_killed)
        self.assertTrue(saved.in_allowlist)
        self.assertTrue(saved.is_quote_token)
        self.assertEqual(saved.metadata, {"name": "Updated contract"})
        self.assertEqual(saved.token_metadata, {"symbol": "NEW"})
        self.assertGreater(saved.updated_at, OLD_TIME)
        fetch_token_metadata.assert_awaited_once_with(
            ctx=self.ctx, address=ADDRESS, token_id="7"
        )

    async def test_unchanged_or_empty_refresh_does_not_advance_cursor(self):
        for metadata, token_metadata in (
            ({"name": "Contract"}, {"symbol": "OLD"}),
            (None, None),
            ({}, {}),
        ):
            with self.subTest(metadata=metadata, token_metadata=token_metadata):
                with patch.object(models.Token, "save", new=AsyncMock()) as save:
                    await self.refresh(metadata, token_metadata, refresh=True)
                    save.assert_not_awaited()
                saved = await models.Token.get(id=self.token.id)
                self.assertEqual(saved.updated_at, OLD_TIME)
                self.assertEqual(saved.metadata, {"name": "Contract"})
                self.assertEqual(saved.token_metadata, {"symbol": "OLD"})

    async def test_only_changed_metadata_field_is_saved(self):
        with patch.object(models.Token, "save", new=AsyncMock()) as save:
            await self.refresh({"name": "Contract"}, {"symbol": "NEW"}, refresh=True)
            save.assert_awaited_once_with(
                update_fields=["token_metadata", "updated_at"]
            )

    async def test_known_metadata_is_not_fetched_without_refresh(self):
        with (
            patch("equiteez.utils.utils.get_contract_metadata", AsyncMock()) as fetch,
            patch(
                "equiteez.utils.utils.get_contract_token_metadata", AsyncMock()
            ) as token_fetch,
            patch("equiteez.utils.utils.get_token_standard", AsyncMock()) as standard,
        ):
            await register_token(self.ctx, ADDRESS, token_id=7)
            fetch.assert_not_awaited()
            token_fetch.assert_not_awaited()
            standard.assert_not_awaited()
        self.assertEqual(
            (await models.Token.get(id=self.token.id)).updated_at, OLD_TIME
        )

    async def test_fa12_zero_enum_value_is_not_refetched(self):
        await models.Token.filter(id=self.token.id).update(
            token_standard=TokenType.FA12
        )
        with patch("equiteez.utils.utils.get_token_standard", AsyncMock()) as fetch:
            await self.refresh({"name": "Contract"}, {"symbol": "OLD"}, refresh=True)
            fetch.assert_not_awaited()

    async def test_missing_standard_is_filled_even_when_value_is_zero(self):
        await models.Token.filter(id=self.token.id).update(token_standard=None)
        with patch(
            "equiteez.utils.utils.get_token_standard",
            AsyncMock(return_value=TokenType.FA12),
        ):
            await self.refresh(None, None, refresh=True)
        saved = await models.Token.get(id=self.token.id)
        self.assertEqual(saved.token_standard, TokenType.FA12)
        self.assertGreater(saved.updated_at, OLD_TIME)


if __name__ == "__main__":
    unittest.main()
