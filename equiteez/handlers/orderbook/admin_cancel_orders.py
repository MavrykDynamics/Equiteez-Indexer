from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.admin_cancel_orders import AdminCancelOrdersParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def admin_cancel_orders(
    ctx: HandlerContext,
    admin_cancel_orders: TezosTransaction[AdminCancelOrdersParameter, OrderbookStorage],
) -> None:
    breakpoint()