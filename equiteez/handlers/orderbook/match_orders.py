from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.match_orders import MatchOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def match_orders(
    ctx: HandlerContext,
    match_orders: TezosTransaction[MatchOrdersParameter, OrderbookStorage],
) -> None:
    breakpoint()