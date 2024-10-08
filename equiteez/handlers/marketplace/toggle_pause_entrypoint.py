from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.toggle_pause_entrypoint import TogglePauseEntrypointParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def toggle_pause_entrypoint(
    ctx: HandlerContext,
    toggle_pause_entrypoint: TezosTransaction[TogglePauseEntrypointParameter, MarketplaceStorage],
) -> None:
    # Fetch operation info
    address                     = toggle_pause_entrypoint.data.target_address
    create_listing_is_paused    = toggle_pause_entrypoint.storage.breakGlassConfig.createListingIsPaused
    edit_listing_is_paused      = toggle_pause_entrypoint.storage.breakGlassConfig.editListingIsPaused
    remove_listing_is_paused    = toggle_pause_entrypoint.storage.breakGlassConfig.removeListingIsPaused
    purchase_is_paused          = toggle_pause_entrypoint.storage.breakGlassConfig.purchaseIsPaused
    offer_is_paused             = toggle_pause_entrypoint.storage.breakGlassConfig.offerIsPaused
    accept_offer_is_paused      = toggle_pause_entrypoint.storage.breakGlassConfig.acceptOfferIsPaused
    remove_offer_is_paused      = toggle_pause_entrypoint.storage.breakGlassConfig.removeOfferIsPaused
    set_currency_is_paused      = toggle_pause_entrypoint.storage.breakGlassConfig.setCurrencyIsPaused

    # Get marketplace
    marketplace                 = await models.Marketplace.get(
        address = address
    )

    # Update record
    marketplace.create_listing_is_paused    = create_listing_is_paused
    marketplace.edit_listing_is_paused      = edit_listing_is_paused
    marketplace.remove_listing_is_paused    = remove_listing_is_paused
    marketplace.purchase_is_paused          = purchase_is_paused
    marketplace.offer_is_paused             = offer_is_paused
    marketplace.accept_offer_is_paused      = accept_offer_is_paused
    marketplace.remove_offer_is_paused      = remove_offer_is_paused
    marketplace.set_currency_is_paused      = set_currency_is_paused
    await marketplace.save()
