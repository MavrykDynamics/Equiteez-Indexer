from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.remove_offer import RemoveOfferParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def remove_offer(
    ctx: HandlerContext,
    remove_offer: TezosTransaction[RemoveOfferParameter, MarketplaceStorage],
) -> None:
    breakpoint()