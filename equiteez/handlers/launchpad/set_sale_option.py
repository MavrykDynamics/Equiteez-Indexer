from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_sale_option import (
    SetSaleOptionParameter,
    SetSaleOptionParameter1,
    SetSaleOptionParameter2,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import upsert_sale_option


async def set_sale_option(
    ctx: HandlerContext,
    set_sale_option: TezosTransaction[SetSaleOptionParameter, LaunchpadStorage],
) -> None:
    address = set_sale_option.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    variant = set_sale_option.parameter.root
    if isinstance(variant, SetSaleOptionParameter1):
        launch_name = variant.createNewSaleOption.launchName
        option_name = variant.createNewSaleOption.saleOption
    elif isinstance(variant, SetSaleOptionParameter2):
        launch_name = variant.updateSaleOption.launchName
        option_name = variant.updateSaleOption.saleOption
    else:
        return

    record = set_sale_option.storage.launchLedger.get(launch_name)
    if not record:
        return
    option_record = record.saleOptions.get(option_name)
    if not option_record:
        return

    launch = await models.LaunchpadLaunch.get(launchpad=launchpad, name=launch_name)
    await upsert_sale_option(ctx, launch, option_name, option_record)
