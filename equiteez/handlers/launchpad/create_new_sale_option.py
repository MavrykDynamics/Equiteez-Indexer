from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.create_new_sale_option import (
    CreateNewSaleOptionParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def create_new_sale_option(
    ctx: HandlerContext,
    create_new_sale_option: TezosTransaction[
        CreateNewSaleOptionParameter, LaunchpadStorage
    ],
) -> None:
    launchpad = await models.Launchpad.get(
        address=create_new_sale_option.data.target_address
    )
    await sync_launches(ctx, launchpad, create_new_sale_option.storage)
