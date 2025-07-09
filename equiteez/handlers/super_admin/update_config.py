from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.update_config import (
    UpdateConfigParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(update_config)
