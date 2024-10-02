from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.update_metadata import UpdateMetadataParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, OrderbookStorage],
) -> None:
    breakpoint()