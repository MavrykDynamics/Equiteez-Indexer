from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def origination(
    ctx: HandlerContext,
    marketplace_origination: TezosOrigination[MarketplaceStorage],
) -> None:
    ...