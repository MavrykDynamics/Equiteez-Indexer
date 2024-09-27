from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosOrigination
from equiteez import models as models
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def origination(
    ctx: HandlerContext,
    orderbook_origination: TezosOrigination[OrderbookStorage],
) -> None:
    ...