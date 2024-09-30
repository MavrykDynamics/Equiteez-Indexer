from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.utils import get_contract_metadata


async def origination(
    ctx: HandlerContext,
    kyc_origination: TezosOrigination[KycStorage],
) -> None:
    # Fetch operation info
    address                         = kyc_origination.data.originated_contract_address
    super_admin                     = kyc_origination.storage.superAdmin
    new_super_admin                 = kyc_origination.storage.newSuperAdmin
    set_member_is_paused            = kyc_origination.storage.breakGlassConfig.setMemberIsPaused
    freeze_member_is_paused         = kyc_origination.storage.breakGlassConfig.freezeMemberIsPaused
    unfreeze_member_is_paused       = kyc_origination.storage.breakGlassConfig.unfreezeMemberIsPaused
    whitelist_ledger                = kyc_origination.storage.whitelistLedger
    blacklist_ledger                = kyc_origination.storage.blacklistLedger
    valid_input_ledger              = kyc_origination.storage.validInputLedger
    kyc_registrar_ledger            = kyc_origination.storage.kycRegistrarLedger
    country_transfer_rule_ledger    = kyc_origination.storage.countryTransferRuleLedger
    member_ledger                   = kyc_origination.storage.memberLedger

    # Prepare the kyc
    kyc = models.Kyc(
        address                         = address,
        super_admin                     = super_admin,
        new_super_admin                 = new_super_admin,
        set_member_is_paused            = set_member_is_paused,
        freeze_member_is_paused         = freeze_member_is_paused,
        unfreeze_member_is_paused       = unfreeze_member_is_paused
    )

    # Get contract metadata
    kyc.metadata = await get_contract_metadata(
        ctx=ctx,
        address=address
    )

    # Save the orderbook
    await kyc.save()

    # Prepare the whitelist ledger
    for whitelist in whitelist_ledger:
        breakpoint

    # Prepare the blacklist ledger
    for whitelist in blacklist_ledger:
        breakpoint

    # Prepare the valid input ledger
    for whitelist in valid_input_ledger:
        breakpoint

    # Prepare the registrar ledger
    for whitelist in kyc_registrar_ledger:
        breakpoint

    # Prepare the country transfer rules ledger
    for whitelist in country_transfer_rule_ledger:
        breakpoint

    # Prepare the member ledger
    for whitelist in member_ledger:
        breakpoint
