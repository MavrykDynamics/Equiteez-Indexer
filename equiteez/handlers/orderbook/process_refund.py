from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.process_refund import ProcessRefundParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def process_refund(
    ctx: HandlerContext,
    process_refund: TezosTransaction[ProcessRefundParameter, OrderbookStorage],
) -> None:
    breakpoint()