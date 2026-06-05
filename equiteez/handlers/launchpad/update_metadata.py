from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_metadata import (
    UpdateMetadataParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.utils import get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, LaunchpadStorage],
) -> None:
    address = update_metadata.data.target_address
    launchpad = await models.Launchpad.get(address=address)
    launchpad.metadata = await get_contract_metadata(ctx=ctx, address=address)
    await launchpad.save()
