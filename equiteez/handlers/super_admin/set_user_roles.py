from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_user_roles import (
    SetUserRolesParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_user_roles(
    ctx: HandlerContext,
    set_user_roles: TezosTransaction[SetUserRolesParameter, SuperAdminStorage],
) -> None:
    # The role / user / contract / updateType parameters are captured in the
    # action data map; the user role ledger itself is only updated once the
    # action is executed via signAction
    await create_super_admin_action(set_user_roles)
