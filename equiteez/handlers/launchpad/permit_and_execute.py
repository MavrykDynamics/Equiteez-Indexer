from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez.types.launchpad.tezos_parameters.permit_and_execute import (
    PermitAndExecuteParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import record_permit_batch


async def permit_and_execute(
    ctx: HandlerContext,
    permit_and_execute: TezosTransaction[PermitAndExecuteParameter, LaunchpadStorage],
) -> None:
    await record_permit_batch(ctx, permit_and_execute)
