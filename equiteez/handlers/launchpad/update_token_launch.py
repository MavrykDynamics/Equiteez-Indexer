from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.update_token_launch import (
    UpdateTokenLaunchParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.launchpad_utils import (
    upsert_launch_from_record,
    upsert_sale_option,
)


async def update_token_launch(
    ctx: HandlerContext,
    update_token_launch: TezosTransaction[UpdateTokenLaunchParameter, LaunchpadStorage],
) -> None:
    address = update_token_launch.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    launch_name = update_token_launch.parameter.launchName
    record = update_token_launch.storage.launchLedger.get(launch_name)
    if not record:
        return

    launch = await upsert_launch_from_record(ctx, launchpad, launch_name, record)

    for option_name, option_record in record.saleOptions.items():
        await upsert_sale_option(ctx, launch, option_name, option_record)
