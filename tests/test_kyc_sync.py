"""KYC ledger removals remain observable to DualCursor clients and reversible."""

import unittest
from datetime import UTC, datetime
from types import SimpleNamespace

from dipdup.models import ModelUpdate, ModelUpdateAction
from dipdup.transactions import TransactionManager
from tortoise import Tortoise

from equiteez import models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc


KYC = "KT1" + "TestKyc".ljust(33, "0")
REGISTRAR = "mv1" + "Registrar".ljust(33, "0")
OTHER_REGISTRAR = "mv1" + "OtherRegistrar".ljust(33, "0")
MEMBER = "mv1" + "Member".ljust(33, "0")
ADMIN = "mv1" + "Admin".ljust(33, "0")
OLD = datetime(2000, 1, 1, tzinfo=UTC)
TRACKED = (
    models.KycRegistrarAdmin,
    models.KycMembershipTier,
    models.KycMembership,
    models.KycMembershipTierDiscount,
)


def storage(**ledgers) -> KycStorage:
    values = dict(
        superAdmin=REGISTRAR,
        metadata={},
        config={"permitDefaultExpiryDuration": "0", "permitMaxExpiryDuration": "0"},
        pauseLedger={},
        membershipTierLedger={},
        membershipTierDiscountLedger=[],
        memberLedger=[],
        memberRegistrarLedger={},
        whitelistLedger={},
        blacklistLedger={},
        validInputLedger={},
        kycRegistrarLedger={},
        kycAdminRegistrarLedger={},
        countryTransferRuleLedger={},
        memberKycLedger={},
        enableKyc=True,
        enableMembership=True,
        lambdaLedger={},
        permitsLedger=[],
        permitsCounterLedger={},
        permitsExpiryLedger=[],
        userPermitsExpiryLedger={},
    )
    values.update(ledgers)
    return KycStorage(**values)


def membership(registrar=REGISTRAR, tier="Gold") -> dict:
    return {"key": {"address_0": registrar, "address_1": MEMBER}, "value": tier}


def discounts(**values) -> dict:
    return {"key": {"address": REGISTRAR, "string": "Gold"}, "value": values}


def member_kyc() -> dict:
    return dict(
        country="FR",
        region="europe",
        investorType="accredited",
        expireAt="2099-01-01T00:00:00Z",
        frozen=False,
        kycRegistrar=REGISTRAR,
    )


def removals(**keys) -> SimpleNamespace:
    return SimpleNamespace(
        diffs=tuple(
            {"path": path, "action": "remove_key", "content": {"key": key}}
            for path, key in keys.items()
        )
    )


class KycSyncTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["dipdup.models", "equiteez.models"]},
        )
        try:
            await Tortoise.generate_schemas()
            self.manager = TransactionManager(depth=5)
            self.registration = self.manager.register()
            await self.registration.__aenter__()
            self.kyc = await models.Kyc.create(address=KYC)
        except BaseException:
            await Tortoise.close_connections()
            raise

    async def asyncTearDown(self):
        await self.registration.__aexit__(None, None, None)
        await Tortoise.close_connections()

    async def sync(self, state=None, **removed):
        kyc = await models.Kyc.get(id=self.kyc.id)
        await sync_kyc(None, kyc, state or storage(), removals(**removed))

    async def age(self, model):
        await model.filter().update(updated_at=OLD)
        return await model.all().first()

    async def assert_tombstone(self, model, row_id, *, removed=True):
        row = await model.get(id=row_id)
        self.assertEqual(row.is_removed, removed)
        self.assertGreater(row.updated_at, OLD)
        return row

    async def test_admin_removal_and_same_row_reassignment(self):
        added = storage(kycAdminRegistrarLedger={ADMIN: REGISTRAR})
        await self.sync(added)
        admin = await self.age(models.KycRegistrarAdmin)
        await self.sync(kycAdminRegistrarLedger=ADMIN)
        await self.assert_tombstone(models.KycRegistrarAdmin, admin.id)
        await self.age(models.KycRegistrarAdmin)
        await self.sync(added)
        revived = await self.assert_tombstone(
            models.KycRegistrarAdmin, admin.id, removed=False
        )
        self.assertEqual(revived.registrar_id, admin.registrar_id)
        await self.sync(kycAdminRegistrarLedger=ADMIN)
        await self.sync(storage(kycAdminRegistrarLedger={ADMIN: OTHER_REGISTRAR}))
        reassigned = await models.KycRegistrarAdmin.get(id=admin.id)
        self.assertNotEqual(reassigned.registrar_id, admin.registrar_id)
        self.assertFalse(reassigned.is_removed)
        self.assertEqual(await models.KycRegistrarAdmin.all().count(), 1)

    async def test_tier_set_shrink_empty_set_removal_and_revival(self):
        await self.sync(storage(membershipTierLedger={REGISTRAR: ["Gold", "Silver"]}))
        await self.age(models.KycMembershipTier)
        gold = await models.KycMembershipTier.get(name="Gold")
        silver = await models.KycMembershipTier.get(name="Silver")
        await self.sync(storage(membershipTierLedger={REGISTRAR: ["Gold"]}))
        await self.assert_tombstone(models.KycMembershipTier, silver.id)
        self.assertFalse((await models.KycMembershipTier.get(id=gold.id)).is_removed)
        await self.sync(storage(membershipTierLedger={REGISTRAR: []}))
        await self.assert_tombstone(models.KycMembershipTier, gold.id)
        await self.age(models.KycMembershipTier)
        await self.sync(storage(membershipTierLedger={REGISTRAR: ["Gold"]}))
        await self.assert_tombstone(models.KycMembershipTier, gold.id, removed=False)
        await self.sync(membershipTierLedger=REGISTRAR)
        await self.assert_tombstone(models.KycMembershipTier, gold.id)
        self.assertEqual(await models.KycMembershipTier.all().count(), 2)

    async def test_discount_map_shrink_empty_map_removal_and_revival(self):
        await self.sync(
            storage(
                membershipTierDiscountLedger=[discounts(exitFee="100", entryFee="50")]
            )
        )
        await self.age(models.KycMembershipTierDiscount)
        exit_fee = await models.KycMembershipTierDiscount.get(discount_name="exitFee")
        entry_fee = await models.KycMembershipTierDiscount.get(discount_name="entryFee")
        await self.sync(
            storage(membershipTierDiscountLedger=[discounts(exitFee="100")])
        )
        await self.assert_tombstone(models.KycMembershipTierDiscount, entry_fee.id)
        self.assertFalse(
            (await models.KycMembershipTierDiscount.get(id=exit_fee.id)).is_removed
        )
        await self.sync(storage(membershipTierDiscountLedger=[discounts()]))
        await self.assert_tombstone(models.KycMembershipTierDiscount, exit_fee.id)
        await self.age(models.KycMembershipTierDiscount)
        await self.sync(
            storage(membershipTierDiscountLedger=[discounts(exitFee="125")])
        )
        revived = await self.assert_tombstone(
            models.KycMembershipTierDiscount, exit_fee.id, removed=False
        )
        self.assertEqual(revived.discount_value, 125)
        await self.sync(
            membershipTierDiscountLedger={"address": REGISTRAR, "string": "Gold"}
        )
        await self.assert_tombstone(models.KycMembershipTierDiscount, exit_fee.id)
        self.assertEqual(await models.KycMembershipTierDiscount.all().count(), 2)

    async def test_membership_removal_clears_verified_tier_and_revival_restores_it(
        self,
    ):
        await self.sync(
            storage(
                memberLedger=[membership(), membership(OTHER_REGISTRAR, "Silver")],
                memberKycLedger={MEMBER: member_kyc()},
            )
        )
        await self.age(models.KycMembership)
        original = await models.KycMembership.get(tier="Gold")
        self.assertEqual((await models.KycMember.get()).membership_tier, "Gold")
        await self.sync(memberLedger={"address_0": REGISTRAR, "address_1": MEMBER})
        await self.assert_tombstone(models.KycMembership, original.id)
        self.assertIsNone((await models.KycMember.get()).membership_tier)
        self.assertFalse((await models.KycMembership.get(tier="Silver")).is_removed)
        # A subsequent KYC-only refresh must also ignore the retained tombstone.
        await self.sync(storage(memberKycLedger={MEMBER: member_kyc()}))
        self.assertIsNone((await models.KycMember.get()).membership_tier)
        await self.age(models.KycMembership)
        await self.sync(storage(memberLedger=[membership()]))
        await self.assert_tombstone(models.KycMembership, original.id, removed=False)
        self.assertEqual((await models.KycMember.get()).membership_tier, "Gold")
        self.assertEqual(await models.KycMembership.all().count(), 2)

    async def test_removed_kyc_record_clears_registrar_and_derived_tier(self):
        await self.sync(
            storage(memberLedger=[membership()], memberKycLedger={MEMBER: member_kyc()})
        )
        await self.sync(memberKycLedger=MEMBER)
        member = await models.KycMember.get()
        self.assertIsNone(member.kyc_registrar_id)
        self.assertIsNone(member.membership_tier)
        self.assertIsNone(member.expire_at)
        self.assertFalse((await models.KycMembership.get()).is_removed)

    async def test_unknown_removals_do_not_create_rows(self):
        await self.sync(
            kycAdminRegistrarLedger=ADMIN,
            membershipTierLedger=REGISTRAR,
            membershipTierDiscountLedger={"address": REGISTRAR, "string": "Gold"},
            memberLedger={"address_0": REGISTRAR, "address_1": MEMBER},
        )
        for model in TRACKED:
            self.assertEqual(await model.all().count(), 0)
        self.assertEqual(await models.EquiteezUser.all().count(), 0)

    async def test_removal_and_revival_are_reversible_updates(self):
        added = storage(
            kycAdminRegistrarLedger={ADMIN: REGISTRAR},
            membershipTierLedger={REGISTRAR: ["Gold"]},
            membershipTierDiscountLedger=[discounts(exitFee="100")],
            memberLedger=[membership()],
            memberKycLedger={MEMBER: member_kyc()},
        )
        await self.sync(added)
        original = {model: await self.age(model) for model in TRACKED}
        async with self.manager.in_transaction(level=100, index="kyc"):
            await self.sync(
                kycAdminRegistrarLedger=ADMIN,
                membershipTierLedger=REGISTRAR,
                membershipTierDiscountLedger={"address": REGISTRAR, "string": "Gold"},
                memberLedger={"address_0": REGISTRAR, "address_1": MEMBER},
            )
        for model in TRACKED:
            update = await ModelUpdate.get(level=100, model_name=model.__name__)
            self.assertEqual(update.action, ModelUpdateAction.UPDATE)
            self.assertEqual(update.data["is_removed"], False)
        async with self.manager.in_transaction(level=101, index="kyc"):
            await self.sync(added)
        # Roll back the revival first, then the original removal.
        for level, removed in ((101, True), (100, False)):
            updates = await ModelUpdate.filter(level=level).order_by("-id")
            for update in updates:
                await update.revert(getattr(models, update.model_name))
            for model in TRACKED:
                row = await model.get(id=original[model].id)
                self.assertEqual(row.is_removed, removed)
            member = await models.KycMember.get()
            self.assertEqual(member.membership_tier, None if removed else "Gold")
        for model in TRACKED:
            row = await model.get(id=original[model].id)
            self.assertEqual(row.updated_at, OLD)


if __name__ == "__main__":
    unittest.main()
