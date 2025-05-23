from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.set_super_admin import SetSuperAdminParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address         = set_super_admin.data.target_address
    new_super_admin = set_super_admin.storage.newSuperAdmin

    # Update dodo mav
    dodo_mav        = await models.DodoMav.get_or_none(
        address = address
    )
    if not dodo_mav:
        return
    dodo_mav.new_super_admin   = new_super_admin
    await dodo_mav.save()
