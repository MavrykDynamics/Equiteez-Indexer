from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.place_sell_order import PlaceSellOrderParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def place_sell_order(
    ctx: HandlerContext,
    place_sell_order: TezosTransaction[PlaceSellOrderParameter, OrderbookStorage],
) -> None:
    breakpoint()