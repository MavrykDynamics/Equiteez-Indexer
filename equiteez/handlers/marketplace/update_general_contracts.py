from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.update_general_contracts import (
    UpdateGeneralContractsParameter,
)
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def update_general_contracts(
    ctx: HandlerContext,
    update_general_contracts: TezosTransaction[
        UpdateGeneralContractsParameter, MarketplaceStorage
    ],
) -> None:
    breakpoint()
