import logging

from dateutil import parser
from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination

from equiteez import models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.contract_allowlist import (
    KYC,
    allowlist_contains,
    fetch_allowlist,
)
from equiteez.utils.dynamic_index import attach_index_kyc
from equiteez.utils.utils import get_contract_metadata

logger = logging.getLogger(__name__)


async def origination(
    ctx: HandlerContext,
    kyc_origination: TezosOrigination[KycStorage],
) -> None:
    address = kyc_origination.data.originated_contract_address
    first_level = kyc_origination.data.level

    if not address:
        return

    await attach_index_kyc(ctx, address, first_level=first_level)

    super_admin = kyc_origination.storage.superAdmin
    new_super_admin = kyc_origination.storage.newSuperAdmin
    whitelist_ledger = kyc_origination.storage.whitelistLedger
    blacklist_ledger = kyc_origination.storage.blacklistLedger
    valid_inputs = kyc_origination.storage.validInputLedger
    kyc_registrars = kyc_origination.storage.kycRegistrarLedger
    country_transfer_rule_ledger = kyc_origination.storage.countryTransferRuleLedger
    member_ledger = kyc_origination.storage.memberLedger
    pause_ledger = kyc_origination.storage.pauseLedger

    kyc, _ = await models.Kyc.get_or_create(address=address)
    kyc.super_admin = super_admin
    kyc.new_super_admin = new_super_admin
    kyc.metadata = await get_contract_metadata(ctx=ctx, address=address)

    allowlist = await fetch_allowlist()
    kyc.in_allowlist = allowlist_contains(allowlist, KYC, address)
    await kyc.save()

    for whitelist_address in whitelist_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=whitelist_address)
        await user.save()
        kyc_whitelist, _ = await models.KycWhitelisted.get_or_create(kyc=kyc, user=user)
        await kyc_whitelist.save()

    for blacklist_address in blacklist_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=blacklist_address)
        await user.save()
        kyc_blacklist, _ = await models.KycBlacklisted.get_or_create(kyc=kyc, user=user)
        await kyc_blacklist.save()

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
        if category == "investor_type":
            investor_types, _ = await models.KycValidInput.get_or_create(
                kyc=kyc, category=models.ValidInputCategory.INVESTOR_TYPE
            )
            investor_types.valid_inputs = valid_input_list
            await investor_types.save()

    for registrar_address in kyc_registrars:
        kyc_registrar = kyc_registrars[registrar_address]
        kyc_admins = kyc_registrar.kycAdmins
        name = kyc_registrar.name
        members_verified = kyc_registrar.membersVerified
        created_at = parser.parse(kyc_registrar.createdAt)
        set_member_paused = kyc_registrar.setMemberIsPaused
        freeze_member_paused = kyc_registrar.freezeMemberIsPaused
        unfreeze_member_paused = kyc_registrar.unfreezeMemberIsPaused
        user, _ = await models.EquiteezUser.get_or_create(address=registrar_address)
        await user.save()
        registrar, _ = await models.KycRegistrar.get_or_create(kyc=kyc, user=user)
        registrar.kyc_admins = kyc_admins
        registrar.name = name
        registrar.members_verified = members_verified
        registrar.created_at = created_at
        registrar.set_member_paused = set_member_paused
        registrar.freeze_member_paused = freeze_member_paused
        registrar.unfreeze_member_paused = unfreeze_member_paused
        await registrar.save()

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

    for member_address in member_ledger:
        member_record = member_ledger[member_address]
        country = member_record.country
        region = member_record.region
        investor_type = member_record.investorType
        frozen = member_record.frozen
        kyc_registrar_address = member_record.kycRegistrar
        registrar, _ = await models.EquiteezUser.get_or_create(
            address=kyc_registrar_address
        )
        await registrar.save()
        kyc_registrar_obj = await models.KycRegistrar.get(kyc=kyc, user=registrar)
        user, _ = await models.EquiteezUser.get_or_create(address=member_address)
        await user.save()
        member, _ = await models.KycMember.get_or_create(kyc=kyc, user=user)
        member.kyc_registrar = kyc_registrar_obj
        member.country = country
        member.region = region
        member.investor_type = investor_type
        if member_record.expireAt:
            member.expire_at = parser.parse(member_record.expireAt)
        member.frozen = frozen
        await member.save()

    for entrypoint in pause_ledger:
        entrypoint_status = models.KycEntrypointStatus(
            contract=kyc, entrypoint=entrypoint, paused=pause_ledger[entrypoint]
        )
        await entrypoint_status.save()

    logger.info("KYC %s registered at level %d", address, first_level)
