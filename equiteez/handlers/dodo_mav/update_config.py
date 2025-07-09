from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_config import UpdateConfigParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, DodoMavStorage],
) -> None:
    # Fetch operations info
    address = update_config.data.target_address
    lp_fee = update_config.storage.config.lpFee
    maintainer_fee = update_config.storage.config.maintainerFee
    fee_decimals = update_config.storage.config.feeDecimals

    # Get dodo mav
    dodo_mav = await models.DodoMav.get_or_none(address=address)
    if not dodo_mav:
        return

    # Update record
    dodo_mav.lp_fee = lp_fee
    dodo_mav.maintainer_fee = maintainer_fee
    dodo_mav.fee_decimals = fee_decimals
    await dodo_mav.save()
