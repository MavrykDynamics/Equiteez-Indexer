from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.transfer import TransferParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def transfer(
    ctx: HandlerContext,
    transfer: TezosTransaction[TransferParameter, SuperAdminStorage],
) -> None:
    # The transfer details are captured in the action data map; the actual
    # MAV / token transfer happens only once the action is executed via
    # signAction
    await create_super_admin_action(transfer)
