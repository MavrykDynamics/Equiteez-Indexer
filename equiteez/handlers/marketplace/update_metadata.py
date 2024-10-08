from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, MarketplaceStorage],
) -> None:
    breakpoint()