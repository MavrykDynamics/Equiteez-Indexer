from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.create_token_launch import (
    CreateTokenLaunchParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def create_token_launch(
    ctx: HandlerContext,
    create_token_launch: TezosTransaction[CreateTokenLaunchParameter, LaunchpadStorage],
) -> None:
    launchpad = await models.Launchpad.get(
        address=create_token_launch.data.target_address
    )
    await sync_launches(ctx, launchpad, create_token_launch.storage)
