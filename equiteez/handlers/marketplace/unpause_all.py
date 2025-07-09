from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.unpause_all import UnpauseAllParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def unpause_all(
    ctx: HandlerContext,
    unpause_all: TezosTransaction[UnpauseAllParameter, MarketplaceStorage],
) -> None:
    # Fetch operation info
    address = unpause_all.data.target_address
    create_listing_is_paused = (
        unpause_all.storage.breakGlassConfig.createListingIsPaused
    )
    edit_listing_is_paused = unpause_all.storage.breakGlassConfig.editListingIsPaused
    remove_listing_is_paused = (
        unpause_all.storage.breakGlassConfig.removeListingIsPaused
    )
    purchase_is_paused = unpause_all.storage.breakGlassConfig.purchaseIsPaused
    offer_is_paused = unpause_all.storage.breakGlassConfig.offerIsPaused
    accept_offer_is_paused = unpause_all.storage.breakGlassConfig.acceptOfferIsPaused
    remove_offer_is_paused = unpause_all.storage.breakGlassConfig.removeOfferIsPaused
    set_currency_is_paused = unpause_all.storage.breakGlassConfig.setCurrencyIsPaused

    # Get marketplace
    marketplace = await models.Marketplace.get(address=address)

    # Update record
    marketplace.create_listing_is_paused = create_listing_is_paused
    marketplace.edit_listing_is_paused = edit_listing_is_paused
    marketplace.remove_listing_is_paused = remove_listing_is_paused
    marketplace.purchase_is_paused = purchase_is_paused
    marketplace.offer_is_paused = offer_is_paused
    marketplace.accept_offer_is_paused = accept_offer_is_paused
    marketplace.remove_offer_is_paused = remove_offer_is_paused
    marketplace.set_currency_is_paused = set_currency_is_paused
    await marketplace.save()
