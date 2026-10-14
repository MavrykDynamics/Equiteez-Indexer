from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_token_launch import (
    UpdateTokenLaunchParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def update_token_launch(
    ctx: HandlerContext,
    update_token_launch: TezosTransaction[UpdateTokenLaunchParameter, LaunchpadStorage],
) -> None:
    # saleOptions, when given, replaces the launch's whole option map
    launchpad = await models.Launchpad.get(
        address=update_token_launch.data.target_address
    )
    await sync_launches(ctx, launchpad, update_token_launch.storage)
