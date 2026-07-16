from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_sale_option import (
    UpdateSaleOptionParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import upsert_sale_option


async def update_sale_option(
    ctx: HandlerContext,
    update_sale_option: TezosTransaction[UpdateSaleOptionParameter, LaunchpadStorage],
) -> None:
    address = update_sale_option.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    launch_name = update_sale_option.parameter.launchName
    option_name = update_sale_option.parameter.saleOption

    record = update_sale_option.storage.launchLedger.get(launch_name)
    if not record:
        return
    option_record = record.saleOptions.get(option_name)
    if not option_record:
        return

    launch = await models.LaunchpadLaunch.get(launchpad=launchpad, name=launch_name)

    # Note: on-chain updateSaleOption only rewrites the sale option record;
    # the launch-level totalBought is NOT recalculated even when the option's
    # totalBought is reset. Resync launch.total_bought from post-op storage
    # anyway as a defensive no-op that heals any prior drift.
    launch.total_bought = int(record.totalBought)
    await launch.save()

    await upsert_sale_option(ctx, launch, option_name, option_record)
