from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.edit_listing import EditListingParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def edit_listing(
    ctx: HandlerContext,
    edit_listing: TezosTransaction[EditListingParameter, MarketplaceStorage],
) -> None:
    breakpoint()