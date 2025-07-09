from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_blacklist import (
    SetBlacklistParameter,
    SetBlacklistAction as addToBlacklist,
)
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_blacklist(
    ctx: HandlerContext,
    set_blacklist: TezosTransaction[SetBlacklistParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = set_blacklist.data.target_address
    set_blacklist_action = set_blacklist.parameter.setBlacklistAction

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Update record
    if type(set_blacklist_action) is addToBlacklist:
        blacklist_addresses = set_blacklist_action.addToBlacklist
        for blacklist_address in blacklist_addresses:
            user, _ = await models.EquiteezUser.get_or_create(address=blacklist_address)
            await user.save()
            kyc_blacklist, _ = await models.KycBlacklisted.get_or_create(
                kyc=kyc, user=user
            )
            await kyc_blacklist.save()
    else:
        blacklist_addresses = set_blacklist_action.removeFromBlacklist
        for blacklist_address in blacklist_addresses:
            user, _ = await models.EquiteezUser.get_or_create(address=blacklist_address)
            await user.save()
            await models.KycBlacklisted.filter(kyc=kyc, user=user).delete()
