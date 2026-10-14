import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.types.launchpad.tezos_storage import SaleOptions
from equiteez.utils.launchpad_utils import upsert_sale_option
from equiteez.utils.utils import NATIVE_MAV_ADDRESS


ADDRESS = "KT1" + "PaymentToken".ljust(33, "0")


def sale_option(currency):
    return SaleOptions.model_validate(
        {
            "totalBought": "0",
            "allowedMembershipTiers": {},
            "payments": {"payment": {"price": "10", "currency": currency}},
            "isPaused": False,
        }
    )


def fa2(token_id):
    return {"fa2": {"tokenContractAddress": ADDRESS, "tokenId": str(token_id)}}


class LaunchpadPaymentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await Tortoise.init(
            db_url="sqlite://:memory:", modules={"models": ["equiteez.models"]}
        )
        await Tortoise.generate_schemas()
        self.transactions = TransactionManager().register()
        await self.transactions.__aenter__()
        self.ctx = SimpleNamespace()
        launchpad = await models.Launchpad.create(address="KT1Launchpad")
        self.launch = await models.LaunchpadLaunch.create(
            launchpad=launchpad, name="launch"
        )

        async def register(ctx, address, token_id=0):
            token, _ = await models.Token.get_or_create(
                address=address, token_id=token_id
            )
            return token

        self.register_patch = patch(
            "equiteez.utils.launchpad_utils.register_token",
            AsyncMock(side_effect=register),
        )
        self.register = self.register_patch.start()

    async def asyncTearDown(self):
        self.register_patch.stop()
        await self.transactions.__aexit__(None, None, None)
        await Tortoise.close_connections()

    async def sync(self, currency):
        option = await upsert_sale_option(
            self.ctx, self.launch, "option", sale_option(currency)
        )
        return await models.LaunchpadSaleOptionPayment.get(
            sale_option=option, name="payment"
        ).prefetch_related("token")

    async def test_nonzero_fa2_payment_uses_requested_asset(self):
        zero = await models.Token.create(address=ADDRESS, token_id=0)
        payment = await self.sync(fa2(7))
        self.assertEqual((payment.token.address, payment.token.token_id), (ADDRESS, 7))
        self.assertNotEqual(payment.token_id, zero.id)
        self.register.assert_awaited_once_with(
            ctx=self.ctx, address=ADDRESS, token_id=7
        )

    async def test_token_id_change_at_same_address_updates_payment(self):
        before = await self.sync(fa2(0))
        after = await self.sync(fa2(7))
        self.assertEqual(before.id, after.id)
        self.assertNotEqual(before.token_id, after.token_id)
        self.assertEqual(after.token.token_id, 7)
        back_to_zero = await self.sync(fa2(0))
        self.assertEqual(back_to_zero.token_id, before.token_id)

    async def test_unchanged_fa2_does_not_register_again(self):
        before = await self.sync(fa2(7))
        self.register.reset_mock()
        after = await self.sync(fa2(7))
        self.assertEqual(before.token_id, after.token_id)
        self.register.assert_not_awaited()

    async def test_fa12_and_native_mav_keep_zero_id(self):
        await self.sync(fa2(7))
        for currency, address in (
            ({"fa12": ADDRESS}, ADDRESS),
            ({"mav": {}}, NATIVE_MAV_ADDRESS),
        ):
            with self.subTest(currency=currency):
                payment = await self.sync(currency)
                self.assertEqual(
                    (payment.token.address, payment.token.token_id), (address, 0)
                )


if __name__ == "__main__":
    unittest.main()
