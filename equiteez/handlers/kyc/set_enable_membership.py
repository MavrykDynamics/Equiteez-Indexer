from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_enable_membership import (
    SetEnableMembershipParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_enable_membership(
    ctx: HandlerContext,
    set_enable_membership: TezosTransaction[SetEnableMembershipParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = set_enable_membership.data.target_address
    enable_membership = set_enable_membership.storage.enableMembership

    # Update kyc
    kyc = await models.Kyc.get(address=address)
    kyc.enable_membership = enable_membership
    await kyc.save()
