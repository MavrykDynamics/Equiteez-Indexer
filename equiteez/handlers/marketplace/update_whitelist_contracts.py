from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.update_whitelist_contracts import UpdateWhitelistContractsParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def update_whitelist_contracts(
    ctx: HandlerContext,
    update_whitelist_contracts: TezosTransaction[UpdateWhitelistContractsParameter, MarketplaceStorage],
) -> None:
    breakpoint()