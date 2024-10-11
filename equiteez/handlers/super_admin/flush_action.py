from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.flush_action import FlushActionParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def flush_action(
    ctx: HandlerContext,
    flush_action: TezosTransaction[FlushActionParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(flush_action)
