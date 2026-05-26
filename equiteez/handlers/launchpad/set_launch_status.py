from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_launch_status import (
    SetLaunchStatusParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import parse_launch_status, parse_ts


async def set_launch_status(
    ctx: HandlerContext,
    set_launch_status: TezosTransaction[SetLaunchStatusParameter, LaunchpadStorage],
) -> None:
    address = set_launch_status.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    launch_name = set_launch_status.parameter.launchName
    record = set_launch_status.storage.launchLedger.get(launch_name)
    if not record:
        return

    launch = await models.LaunchpadLaunch.get(launchpad=launchpad, name=launch_name)
    launch.status = parse_launch_status(record.status)
    launch.sale_closed = parse_ts(record.saleClosed)
    launch.is_paused = record.isPaused
    await launch.save()
