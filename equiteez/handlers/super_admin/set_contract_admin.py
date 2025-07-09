from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_contract_admin import (
    SetContractAdminParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_contract_admin(
    ctx: HandlerContext,
    set_contract_admin: TezosTransaction[SetContractAdminParameter, SuperAdminStorage],
) -> None:
    await create_super_admin_action(set_contract_admin)
