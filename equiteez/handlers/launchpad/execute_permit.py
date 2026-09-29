from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez.types.launchpad.tezos_parameters.execute_permit import (
    ExecutePermitParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import record_permit_batch


async def execute_permit(
    ctx: HandlerContext,
    execute_permit: TezosTransaction[ExecutePermitParameter, LaunchpadStorage],
) -> None:
    await record_permit_batch(ctx, execute_permit)
