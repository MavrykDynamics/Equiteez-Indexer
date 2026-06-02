from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.claim_super_admin import (
    ClaimSuperAdminParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, LaunchpadStorage],
) -> None:
    address = claim_super_admin.data.target_address
    launchpad = await models.Launchpad.get(address=address)
    launchpad.super_admin = claim_super_admin.storage.superAdmin
    launchpad.new_super_admin = claim_super_admin.storage.newSuperAdmin
    await launchpad.save()
