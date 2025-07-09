from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.create_listing import (
    CreateListingParameter,
)
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def create_listing(
    ctx: HandlerContext,
    create_listing: TezosTransaction[CreateListingParameter, MarketplaceStorage],
) -> None:
    breakpoint()
