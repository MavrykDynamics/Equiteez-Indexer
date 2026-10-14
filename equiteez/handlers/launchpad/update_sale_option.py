from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_sale_option import (
    UpdateSaleOptionParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def update_sale_option(
    ctx: HandlerContext,
    update_sale_option: TezosTransaction[UpdateSaleOptionParameter, LaunchpadStorage],
) -> None:
    launchpad = await models.Launchpad.get(
        address=update_sale_option.data.target_address
    )
    await sync_launches(ctx, launchpad, update_sale_option.storage)
