from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.update_guide_price import (
    UpdateGuidePriceParameter,
)
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def update_guide_price(
    ctx: HandlerContext,
    update_guide_price: TezosTransaction[UpdateGuidePriceParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address = update_guide_price.data.target_address
    guide_price = update_guide_price.storage.guidePrice

    # Update dodo mav
    dodo_mav = await models.DodoMav.get_or_none(address=address)
    if not dodo_mav:
        return
    dodo_mav.guide_price = guide_price
    await dodo_mav.save()
