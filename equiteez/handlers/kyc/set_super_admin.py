from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_super_admin import SetSuperAdminParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, KycStorage],
) -> None:
    # Fetch operation info
    address         = set_super_admin.data.target_address
    new_super_admin = set_super_admin.storage.newSuperAdmin

    # Update kyc
    kyc             = await models.Kyc.get(
        address = address
    )
    kyc.new_super_admin   = new_super_admin
    await kyc.save()
