from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.kill_token import KillTokenParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def kill_token(
    ctx: HandlerContext,
    kill_token: TezosTransaction[KillTokenParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(kill_token)
