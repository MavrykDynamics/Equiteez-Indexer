from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_treasury import SetTreasuryParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def set_treasury(
    ctx: HandlerContext,
    set_treasury: TezosTransaction[SetTreasuryParameter, LaunchpadStorage],
) -> None:
    address = set_treasury.data.target_address
    launchpad = await models.Launchpad.get(address=address)

    treasury, _ = await models.LaunchpadTreasury.get_or_create(
        launchpad=launchpad,
        name=set_treasury.parameter.treasuryName,
        defaults={"address": set_treasury.parameter.treasuryAddress},
    )
    if treasury.address != set_treasury.parameter.treasuryAddress:
        treasury.address = set_treasury.parameter.treasuryAddress
        await treasury.save()
