from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.contract_allowlist import (
    KYC,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.utils import get_contract_metadata
from dateutil import parser


async def origination(
    ctx: HandlerContext,
    kyc_origination: TezosOrigination[KycStorage],
) -> None:
    # Fetch operation info
    address = kyc_origination.data.originated_contract_address

    if not address:
        return

    super_admin = kyc_origination.storage.superAdmin
    new_super_admin = kyc_origination.storage.newSuperAdmin
    enable_kyc = kyc_origination.storage.enableKyc
    enable_membership = kyc_origination.storage.enableMembership
    whitelist_ledger = kyc_origination.storage.whitelistLedger
    blacklist_ledger = kyc_origination.storage.blacklistLedger
    valid_inputs = kyc_origination.storage.validInputLedger
    kyc_registrars = kyc_origination.storage.kycRegistrarLedger
    country_transfer_rule_ledger = kyc_origination.storage.countryTransferRuleLedger
    membership_tier_ledger = kyc_origination.storage.membershipTierLedger
    member_ledger = kyc_origination.storage.memberLedger
    member_kyc_ledger = kyc_origination.storage.memberKycLedger
    pause_ledger = kyc_origination.storage.pauseLedger

    # Prepare the kyc
    kyc, _ = await models.Kyc.get_or_create(address=address)
    kyc.super_admin = super_admin
    kyc.new_super_admin = new_super_admin
    kyc.enable_kyc = enable_kyc
    kyc.enable_membership = enable_membership

    # Get contract metadata
    kyc.metadata = await get_contract_metadata(ctx=ctx, address=address)

    allowlist = await fetch_allowlist()
    kyc.in_allowlist = allowlist_contains(allowlist, KYC, address)

    # Save the orderbook
    await kyc.save()

    # Prepare the whitelist ledger
    for whitelist_address in whitelist_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=whitelist_address)
        await user.save()
        kyc_whitelist, _ = await models.KycWhitelisted.get_or_create(kyc=kyc, user=user)
        await kyc_whitelist.save()

    # Prepare the blacklist ledger
    for blacklist_address in blacklist_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=blacklist_address)
        await user.save()
        kyc_blacklist, _ = await models.KycBlacklisted.get_or_create(kyc=kyc, user=user)
        await kyc_blacklist.save()

    # Prepare the valid input ledger
    for category in valid_inputs:
        valid_input_list = valid_inputs[category]
        if category == "country":
            countries, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.COUNTRY
            )
            countries.valid_inputs = valid_input_list
            await countries.save()
        if category == "region":
            regions, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.REGION
            )
            regions.valid_inputs = valid_input_list
            await regions.save()
        if category == "investorType":
            investor_types, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.INVESTOR_TYPE
            )
            investor_types.valid_inputs = valid_input_list
            await investor_types.save()

    # Prepare the registrar ledger
    for registrar_address in kyc_registrars:
        kyc_registrar = kyc_registrars[registrar_address]
        kyc_admins = kyc_registrar.kycAdmins
        name = kyc_registrar.name
        members_verified = kyc_registrar.membersVerified
        created_at = parser.parse(kyc_registrar.createdAt)
        set_member_kyc_paused = kyc_registrar.setMemberKycIsPaused
        freeze_member_paused = kyc_registrar.freezeMemberIsPaused
        unfreeze_member_paused = kyc_registrar.unfreezeMemberIsPaused
        user, _ = await models.EquiteezUser.get_or_create(address=registrar_address)
        await user.save()
        registrar, _ = await models.KycRegistrar.get_or_create(kyc=kyc, user=user)
        registrar.kyc_admins = kyc_admins
        registrar.name = name
        registrar.member_verified = int(members_verified)
        registrar.created_at = created_at
        registrar.set_member_kyc_is_paused = set_member_kyc_paused
        registrar.freeze_member_is_paused = freeze_member_paused
        registrar.unfreeze_member_is_paused = unfreeze_member_paused
        await registrar.save()

    # Prepare the country transfer rules ledger
    for country in country_transfer_rule_ledger:
        transfer_rule = country_transfer_rule_ledger[country]
        whitelist_countries = transfer_rule.whitelistCountries
        blacklist_countries = transfer_rule.blacklistCountries
        sending_frozen = transfer_rule.sendingFrozen
        receiving_frozen = transfer_rule.receivingFrozen
        country_transfer_rule, _ = await models.KycCountryTransferRule.get_or_create(
            kyc=kyc, country=country
        )
        country_transfer_rule.whitelist_countries = whitelist_countries
        country_transfer_rule.blacklist_countries = blacklist_countries
        country_transfer_rule.sending_frozen = sending_frozen
        country_transfer_rule.receiving_frozen = receiving_frozen
        await country_transfer_rule.save()

    # Prepare the membership tier ledger
    for tier_item in membership_tier_ledger:
        discount, _ = await models.KycMembershipTierDiscount.get_or_create(
            kyc=kyc,
            membership_tier=tier_item.key.string_0,
            discount_name=tier_item.key.string_1,
        )
        discount.discount_value = int(tier_item.value)
        await discount.save()

    # Prepare the member ledger
    for member_address in member_ledger:
        membership_tier = member_ledger[member_address]
        user, _ = await models.EquiteezUser.get_or_create(address=member_address)
        await user.save()
        member, _ = await models.KycMember.get_or_create(kyc=kyc, user=user)
        member.membership_tier = membership_tier
        await member.save()

    # Prepare the member kyc ledger
    for member_address in member_kyc_ledger:
        member_record = member_kyc_ledger[member_address]
        country = member_record.country
        region = member_record.region
        investor_type = member_record.investorType
        frozen = member_record.frozen
        kyc_registrar_address = member_record.kycRegistrar
        registrar, _ = await models.EquiteezUser.get_or_create(
            address=kyc_registrar_address
        )
        await registrar.save()
        kyc_registrar = await models.KycRegistrar.get(kyc=kyc, user=registrar)
        user, _ = await models.EquiteezUser.get_or_create(address=member_address)
        await user.save()
        member, _ = await models.KycMember.get_or_create(kyc=kyc, user=user)
        member.kyc_registrar = kyc_registrar
        member.country = country
        member.region = region
        member.investor_type = investor_type
        if member_record.expireAt:
            member.expire_at = parser.parse(member_record.expireAt)
        member.frozen = frozen
        await member.save()

    # Save the entrypoints status
    for entrypoint in pause_ledger:
        paused = pause_ledger[entrypoint]
        entrypoint_status = models.KycEntrypointStatus(
            contract=kyc, entrypoint=entrypoint, paused=paused
        )
        await entrypoint_status.save()
