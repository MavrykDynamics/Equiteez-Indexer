from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.remove_listing import (
    RemoveListingParameter,
)
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def remove_listing(
    ctx: HandlerContext,
    remove_listing: TezosTransaction[RemoveListingParameter, MarketplaceStorage],
) -> None:
    breakpoint()
