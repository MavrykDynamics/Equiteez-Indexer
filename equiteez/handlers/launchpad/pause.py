from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.pause import PauseParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def pause(
    ctx: HandlerContext,
    pause: TezosTransaction[PauseParameter, LaunchpadStorage],
) -> None:
    address = pause.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    for item in pause.parameter.root:
        status, _ = await models.LaunchpadEntrypointStatus.get_or_create(
            contract=launchpad, entrypoint=item.entrypoint
        )
        status.paused = item.pauseBool
        await status.save()
