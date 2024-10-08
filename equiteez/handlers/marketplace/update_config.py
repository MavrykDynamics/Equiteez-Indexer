from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.update_config import UpdateConfigParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def update_config(
    ctx: HandlerContext,
    update_config: TezosTransaction[UpdateConfigParameter, MarketplaceStorage],
) -> None:
    # Fetch operation info
    address             = update_config.data.target_address
    min_offer_amount    = update_config.storage.config.minOfferAmount
    standard_unit       = update_config.storage.config.standardUnit
    royalty             = update_config.storage.config.royalty
    marketplace_fee     = update_config.storage.config.marketplaceFee

    # Get marketplace
    marketplace                 = await models.Marketplace.get(
        address = address
    )

    # Update record
    marketplace.min_offer_amount    = min_offer_amount
    marketplace.standard_unit       = standard_unit
    marketplace.royalty             = royalty
    marketplace.marketplace_fee     = marketplace_fee
    await marketplace.save()
