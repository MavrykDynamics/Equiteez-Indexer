from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.pause import PauseParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def pause(
    ctx: HandlerContext,
    pause: TezosTransaction[PauseParameter, SuperAdminStorage],
) -> None:
    # The super admin holds no pause state of its own: the entrypoint list and
    # target contract address are captured in the action data map, and the
    # pause is only forwarded to the target contract once the action is
    # executed via signAction, where it is indexed by the target contract
    # pause handler
    await create_super_admin_action(pause)
