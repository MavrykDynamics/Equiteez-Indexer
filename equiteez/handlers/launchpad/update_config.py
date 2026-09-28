from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_config import (
    UpdateConfigParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import apply_launchpad_config


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, LaunchpadStorage],
) -> None:
    launchpad = await models.Launchpad.get(address=update_config.data.target_address)
    apply_launchpad_config(launchpad, update_config.storage.config)
    await launchpad.save()
