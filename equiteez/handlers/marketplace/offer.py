from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.offer import OfferParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def offer(
    ctx: HandlerContext,
    offer: TezosTransaction[OfferParameter, MarketplaceStorage],
) -> None:
    breakpoint()
