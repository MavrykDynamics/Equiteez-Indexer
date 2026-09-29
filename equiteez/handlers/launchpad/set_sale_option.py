from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_sale_option import (
    SetSaleOptionParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import sync_launches


async def set_sale_option(
    ctx: HandlerContext,
    set_sale_option: TezosTransaction[SetSaleOptionParameter, LaunchpadStorage],
) -> None:
    # The wrapper entrypoint of createNewSaleOption / updateSaleOption; either
    # branch can also be called directly
    launchpad = await models.Launchpad.get(address=set_sale_option.data.target_address)
    await sync_launches(ctx, launchpad, set_sale_option.storage)
