from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.accept_offer import AcceptOfferParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def accept_offer(
    ctx: HandlerContext,
    accept_offer: TezosTransaction[AcceptOfferParameter, MarketplaceStorage],
) -> None:
    breakpoint()