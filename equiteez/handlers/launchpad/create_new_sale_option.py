from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.create_new_sale_option import (
    CreateNewSaleOptionParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import upsert_sale_option


async def create_new_sale_option(
    ctx: HandlerContext,
    create_new_sale_option: TezosTransaction[
        CreateNewSaleOptionParameter, LaunchpadStorage
    ],
) -> None:
    address = create_new_sale_option.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    launch_name = create_new_sale_option.parameter.launchName
    option_name = create_new_sale_option.parameter.saleOption

    record = create_new_sale_option.storage.launchLedger.get(launch_name)
    if not record:
        return
    option_record = record.saleOptions.get(option_name)
    if not option_record:
        return

    launch = await models.LaunchpadLaunch.get(launchpad=launchpad, name=launch_name)
    await upsert_sale_option(ctx, launch, option_name, option_record)
