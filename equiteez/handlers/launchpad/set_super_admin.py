from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_super_admin import (
    SetSuperAdminParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, LaunchpadStorage],
) -> None:
    address = set_super_admin.data.target_address
    launchpad = await models.Launchpad.get(address=address)
    launchpad.new_super_admin = set_super_admin.storage.newSuperAdmin
    await launchpad.save()
