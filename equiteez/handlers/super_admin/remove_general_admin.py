from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.remove_general_admin import RemoveGeneralAdminParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def remove_general_admin(
    ctx: HandlerContext,
    remove_general_admin: TezosTransaction[RemoveGeneralAdminParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(remove_general_admin)
