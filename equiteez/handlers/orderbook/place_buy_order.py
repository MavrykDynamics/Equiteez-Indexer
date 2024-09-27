from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_buy_order import PlaceBuyOrderParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def place_buy_order(
    ctx: HandlerContext,
    place_buy_order: TezosTransaction[PlaceBuyOrderParameter, OrderbookStorage],
) -> None:
    ...