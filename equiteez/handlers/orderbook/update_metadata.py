from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.update_metadata import (
    UpdateMetadataParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import get_contract_metadata


async def update_metadata(
    ctx: HandlerContext,
    update_metadata: TezosTransaction[UpdateMetadataParameter, OrderbookStorage],
) -> None:
    # Fetch operations info
    address = update_metadata.data.target_address

    # Get orderbook
    orderbook = await models.Orderbook.get(address=address)

    # Update record
    orderbook.metadata = await get_contract_metadata(ctx=ctx, address=address)
