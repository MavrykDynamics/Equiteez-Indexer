from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_general_admin import SetGeneralAdminParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_general_admin(
    ctx: HandlerContext,
    set_general_admin: TezosTransaction[SetGeneralAdminParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(set_general_admin)
