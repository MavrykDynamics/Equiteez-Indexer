"""
Mirror of the membership KYC contract.

Every ledger of the contract is a big map, so a handler's typed storage holds
exactly the keys the operation added or updated, and the raw diffs hold the
keys it removed. Replaying both is enough to mirror any entrypoint, including
the actions a permit batch dispatches on a signer's behalf, without
re-implementing each entrypoint's parameter handling.
"""

from typing import Any

from dateutil import parser
from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOperationData

from equiteez import models as models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.permits import removed_bigmap_keys

_VALID_INPUT_CATEGORIES = {
    "country": models.ValidInputCategory.COUNTRY,
    "region": models.ValidInputCategory.REGION,
    "investorType": models.ValidInputCategory.INVESTOR_TYPE,
}


async def _user(address: str) -> "models.EquiteezUser":
    user, _ = await models.EquiteezUser.get_or_create(address=address)
    return user


async def _registrar(kyc: "models.Kyc", address: str) -> "models.KycRegistrar":
    registrar, _ = await models.KycRegistrar.get_or_create(
        kyc=kyc, user=await _user(address)
    )
    return registrar


async def _registrar_or_none(
    kyc: "models.Kyc", address: str
) -> "models.KycRegistrar | None":
    return await models.KycRegistrar.get_or_none(kyc=kyc, user__address=address)


def _key_field(key: Any, name: str) -> str:
    return key[name] if isinstance(key, dict) else getattr(key, name)


async def _sync_registrars(kyc: "models.Kyc", storage: KycStorage) -> None:
    for address, record in storage.kycRegistrarLedger.items():
        registrar = await _registrar(kyc, address)
        registrar.name = record.name
        registrar.member_verified = int(record.membersVerified)
        registrar.created_at = parser.parse(record.createdAt)
        registrar.set_member_is_paused = record.setMemberIsPaused
        registrar.set_member_kyc_is_paused = record.setMemberKycIsPaused
        registrar.freeze_member_is_paused = record.freezeMemberIsPaused
        registrar.set_registrar_admin_is_paused = record.setRegistrarAdminIsPaused
        await registrar.save()


async def _sync_registrar_admins(
    kyc: "models.Kyc", storage: KycStorage, data: TezosOperationData
) -> None:
    for admin_address, registrar_address in storage.kycAdminRegistrarLedger.items():
        registrar = await _registrar(kyc, registrar_address)
        admin, _ = await models.KycRegistrarAdmin.get_or_create(
            kyc=kyc, user=await _user(admin_address), defaults={"registrar": registrar}
        )
        if admin.registrar_id != registrar.id:
            admin.registrar = registrar
            await admin.save()
    for admin_address in removed_bigmap_keys(data, "kycAdminRegistrarLedger"):
        user = await models.EquiteezUser.get_or_none(address=admin_address)
        if user:
            await models.KycRegistrarAdmin.filter(kyc=kyc, user=user).delete()


async def _sync_membership_tiers(
    kyc: "models.Kyc", storage: KycStorage, data: TezosOperationData
) -> None:
    # registrar -> set(tier): the value is the registrar's full tier set
    for registrar_address, tier_names in storage.membershipTierLedger.items():
        registrar = await _registrar(kyc, registrar_address)
        await (
            models.KycMembershipTier.filter(kyc=kyc, registrar=registrar)
            .exclude(name__in=list(tier_names))
            .delete()
        )
        for tier_name in tier_names:
            await models.KycMembershipTier.get_or_create(
                kyc=kyc, registrar=registrar, name=tier_name
            )
    for registrar_address in removed_bigmap_keys(data, "membershipTierLedger"):
        registrar = await _registrar_or_none(kyc, registrar_address)
        if registrar:
            await models.KycMembershipTier.filter(kyc=kyc, registrar=registrar).delete()


async def _sync_tier_discounts(
    kyc: "models.Kyc", storage: KycStorage, data: TezosOperationData
) -> None:
    # (registrar, tier) -> map(discount name -> basis points), the full map
    for item in storage.membershipTierDiscountLedger:
        registrar = await _registrar(kyc, item.key.address)
        tier_name = item.key.string
        await (
            models.KycMembershipTierDiscount.filter(
                kyc=kyc, registrar=registrar, membership_tier=tier_name
            )
            .exclude(discount_name__in=list(item.value))
            .delete()
        )
        for discount_name, discount_value in item.value.items():
            discount, _ = await models.KycMembershipTierDiscount.get_or_create(
                kyc=kyc,
                registrar=registrar,
                membership_tier=tier_name,
                discount_name=discount_name,
            )
            discount.discount_value = int(discount_value)
            await discount.save()
    for key in removed_bigmap_keys(data, "membershipTierDiscountLedger"):
        registrar = await _registrar_or_none(kyc, _key_field(key, "address"))
        if registrar:
            await models.KycMembershipTierDiscount.filter(
                kyc=kyc, registrar=registrar, membership_tier=_key_field(key, "string")
            ).delete()


async def _sync_memberships(
    kyc: "models.Kyc", storage: KycStorage, data: TezosOperationData
) -> set[str]:
    """Mirror (registrar, member) -> tier; returns the members touched."""
    touched: set[str] = set()
    for item in storage.memberLedger:
        registrar = await _registrar(kyc, item.key.address_0)
        membership, _ = await models.KycMembership.get_or_create(
            kyc=kyc,
            registrar=registrar,
            user=await _user(item.key.address_1),
            defaults={"tier": item.value},
        )
        if membership.tier != item.value:
            membership.tier = item.value
            await membership.save()
        touched.add(item.key.address_1)
    for key in removed_bigmap_keys(data, "memberLedger"):
        member_address = _key_field(key, "address_1")
        registrar = await _registrar_or_none(kyc, _key_field(key, "address_0"))
        user = await models.EquiteezUser.get_or_none(address=member_address)
        if registrar and user:
            await models.KycMembership.filter(
                kyc=kyc, registrar=registrar, user=user
            ).delete()
        touched.add(member_address)
    return touched


async def _sync_address_list(
    kyc: "models.Kyc",
    model: type["models.KycWhitelisted"] | type["models.KycBlacklisted"],
    added: dict[str, Any],
    removed: list[str],
) -> None:
    for address in added:
        await model.get_or_create(kyc=kyc, user=await _user(address))
    for address in removed:
        user = await models.EquiteezUser.get_or_none(address=address)
        if user:
            await model.filter(kyc=kyc, user=user).delete()


async def _sync_valid_inputs(kyc: "models.Kyc", storage: KycStorage) -> None:
    for category_name, values in storage.validInputLedger.items():
        category = _VALID_INPUT_CATEGORIES.get(category_name)
        if category is None:
            continue
        valid_input, _ = await models.KycValidInput.get_or_create(
            kyc=kyc, category=category
        )
        valid_input.valid_inputs = list(values)
        await valid_input.save()


async def _sync_country_transfer_rules(kyc: "models.Kyc", storage: KycStorage) -> None:
    for country, rule in storage.countryTransferRuleLedger.items():
        transfer_rule, _ = await models.KycCountryTransferRule.get_or_create(
            kyc=kyc, country=country
        )
        transfer_rule.whitelist_countries = list(rule.whitelistCountries)
        transfer_rule.blacklist_countries = list(rule.blacklistCountries)
        transfer_rule.sending_frozen = rule.sendingFrozen
        transfer_rule.receiving_frozen = rule.receivingFrozen
        await transfer_rule.save()


async def _sync_member_kyc(
    kyc: "models.Kyc", storage: KycStorage, data: TezosOperationData
) -> set[str]:
    """Mirror member -> KYC record; returns the members touched."""
    touched: set[str] = set()
    for member_address, record in storage.memberKycLedger.items():
        member, _ = await models.KycMember.get_or_create(
            kyc=kyc, user=await _user(member_address)
        )
        member.kyc_registrar = await _registrar(kyc, record.kycRegistrar)
        member.country = record.country
        member.region = record.region
        member.investor_type = record.investorType
        member.expire_at = parser.parse(record.expireAt) if record.expireAt else None
        member.frozen = record.frozen
        await member.save()
        touched.add(member_address)
    # RemoveMemberKyc: keep the row (and its history) but clear the KYC data
    for member_address in removed_bigmap_keys(data, "memberKycLedger"):
        member = await models.KycMember.get_or_none(
            kyc=kyc, user__address=member_address
        )
        if member:
            member.kyc_registrar = None
            member.country = None
            member.region = None
            member.investor_type = None
            member.expire_at = None
            member.frozen = False
            await member.save()
        touched.add(member_address)
    return touched


async def _refresh_member_tiers(kyc: "models.Kyc", member_addresses: set[str]) -> None:
    """KycMember.membership_tier is the tier under the registrar that verified
    the member's KYC, the one the launchpad and orderbooks price against."""
    for member_address in member_addresses:
        member = await models.KycMember.get_or_none(
            kyc=kyc, user__address=member_address
        )
        if member is None:
            continue
        tier = None
        if member.kyc_registrar_id is not None:
            membership = await models.KycMembership.get_or_none(
                kyc=kyc,
                registrar_id=member.kyc_registrar_id,
                user_id=member.user_id,
            )
            tier = membership.tier if membership else None
        if member.membership_tier != tier:
            member.membership_tier = tier
            await member.save()


async def _sync_pause_ledger(kyc: "models.Kyc", storage: KycStorage) -> None:
    for entrypoint, paused in storage.pauseLedger.items():
        entrypoint_status, _ = await models.KycEntrypointStatus.get_or_create(
            contract=kyc, entrypoint=entrypoint
        )
        entrypoint_status.paused = paused
        await entrypoint_status.save()


async def sync_kyc(
    ctx: HandlerContext,
    kyc: "models.Kyc",
    storage: KycStorage,
    data: TezosOperationData,
) -> None:
    kyc.super_admin = storage.superAdmin
    kyc.new_super_admin = storage.newSuperAdmin
    kyc.enable_kyc = storage.enableKyc
    kyc.enable_membership = storage.enableMembership
    kyc.permit_default_expiry_duration = int(storage.config.permitDefaultExpiryDuration)
    kyc.permit_max_expiry_duration = int(storage.config.permitMaxExpiryDuration)
    await kyc.save()

    await _sync_registrars(kyc, storage)
    await _sync_registrar_admins(kyc, storage, data)
    await _sync_membership_tiers(kyc, storage, data)
    await _sync_tier_discounts(kyc, storage, data)
    touched = await _sync_memberships(kyc, storage, data)
    await _sync_address_list(
        kyc,
        models.KycWhitelisted,
        storage.whitelistLedger,
        list(removed_bigmap_keys(data, "whitelistLedger")),
    )
    await _sync_address_list(
        kyc,
        models.KycBlacklisted,
        storage.blacklistLedger,
        list(removed_bigmap_keys(data, "blacklistLedger")),
    )
    await _sync_valid_inputs(kyc, storage)
    await _sync_country_transfer_rules(kyc, storage)
    touched |= await _sync_member_kyc(kyc, storage, data)
    await _refresh_member_tiers(kyc, touched)
    await _sync_pause_ledger(kyc, storage)


async def sync_kyc_operation(ctx: HandlerContext, transaction) -> None:
    """Handler body shared by every state-changing KYC entrypoint."""
    kyc = await models.Kyc.get(address=transaction.data.target_address)
    await sync_kyc(ctx, kyc, transaction.storage, transaction.data)
