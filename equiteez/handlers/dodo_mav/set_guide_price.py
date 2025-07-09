from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.set_guide_price import (
    SetGuidePriceParameter,
)
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage


async def set_guide_price(
    ctx: HandlerContext,
    set_guide_price: TezosTransaction[SetGuidePriceParameter, DodoMavStorage],
) -> None:
    # Fetch operation info
    address = set_guide_price.data.target_address
    price_model = set_guide_price.storage.guidePriceConfig.priceModel
    appraisal_price = set_guide_price.storage.guidePriceConfig.appraisalPrice
    fixed_price_percent = set_guide_price.storage.guidePriceConfig.fixedPricePercent
    orderbook_price_percent = (
        set_guide_price.storage.guidePriceConfig.orderbookPricePercent
    )

    # Update dodo mav
    price_model_enum = models.PriceModel.FIXED
    if price_model != "fixed":
        price_model_enum = models.PriceModel.DYNAMIC
    dodo_mav = await models.DodoMav.get_or_none(address=address)
    if not dodo_mav:
        return
    dodo_mav.price_model = price_model_enum
    dodo_mav.appraisal_price = appraisal_price
    dodo_mav.fixed_price_percent = fixed_price_percent
    dodo_mav.orderbook_price_percent = orderbook_price_percent
    await dodo_mav.save()
