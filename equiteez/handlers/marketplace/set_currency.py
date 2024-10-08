from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.set_currency import SetCurrencyParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def set_currency(
    ctx: HandlerContext,
    set_currency: TezosTransaction[SetCurrencyParameter, MarketplaceStorage],
) -> None:
    breakpoint()