from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.claim_super_admin import ClaimSuperAdminParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address         = claim_super_admin.data.target_address
    new_super_admin = claim_super_admin.storage.newSuperAdmin
    super_admin     = claim_super_admin.storage.superAdmin

    # Update dodo mav
    dodo_mav        = await models.DodoMav.get_or_none(
        address = address
    )
    if not dodo_mav:
        return
    dodo_mav.new_super_admin   = new_super_admin
    dodo_mav.super_admin       = super_admin
    await dodo_mav.save()
