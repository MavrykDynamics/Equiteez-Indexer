from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.claim_super_admin import (
    ClaimSuperAdminParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, KycStorage],
) -> None:
    # Fetch operation info
    address = claim_super_admin.data.target_address
    new_super_admin = claim_super_admin.storage.newSuperAdmin
    super_admin = claim_super_admin.storage.superAdmin

    # Update kyc
    kyc = await models.Kyc.get(address=address)
    kyc.new_super_admin = new_super_admin
    kyc.super_admin = super_admin
    await kyc.save()
