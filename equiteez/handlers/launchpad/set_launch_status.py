from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_launch_status import (
    SetLaunchStatusParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def set_launch_status(
    ctx: HandlerContext,
    set_launch_status: TezosTransaction[SetLaunchStatusParameter, LaunchpadStorage],
) -> None:
    # CLOSED stamps saleClosed and clears isPaused; isPaused is true only
    # while the status is PAUSED
    launchpad = await models.Launchpad.get(
        address=set_launch_status.data.target_address
    )
    await sync_launches(ctx, launchpad, set_launch_status.storage)
