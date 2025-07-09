from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.purchase import PurchaseParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def purchase(
    ctx: HandlerContext,
    purchase: TezosTransaction[PurchaseParameter, MarketplaceStorage],
) -> None:
    breakpoint()
