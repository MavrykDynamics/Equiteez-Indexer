from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_whitelist import SetWhitelistParameter, SetWhitelistAction as addToWhitelist
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_whitelist(
    ctx: HandlerContext,
    set_whitelist: TezosTransaction[SetWhitelistParameter, KycStorage],
) -> None:
    # Fetch operation info
    address                 = set_whitelist.data.target_address
    set_whitelist_action    = set_whitelist.parameter.setWhitelistAction

    # Get kyc
    kyc         = await models.Kyc.get(
        address = address
    )

    # Update record
    if type(set_whitelist_action) == addToWhitelist:
        whitelist_addresses = set_whitelist_action.addToWhitelist
        for whitelist_address in whitelist_addresses:
            user, _             = await models.EquiteezUser.get_or_create(
                address = whitelist_address
            )
            await user.save()
            kyc_whitelist, _    = await models.KycWhitelisted.get_or_create(
                kyc     = kyc,
                user    = user
            )
            await kyc_whitelist.save()
    else:
        whitelist_addresses = set_whitelist_action.removeFromWhitelist
        for whitelist_address in whitelist_addresses:
            user, _             = await models.EquiteezUser.get_or_create(
                address = whitelist_address
            )
            await user.save()
            await models.KycWhitelisted.filter(
                kyc     = kyc,
                user    = user
            ).delete()
