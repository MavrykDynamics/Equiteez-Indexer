from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.execute_permit import (
    ExecutePermitParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_permit_batch


async def execute_permit(
    ctx: HandlerContext,
    execute_permit: TezosTransaction[ExecutePermitParameter, OrderbookStorage],
) -> None:
    await record_permit_batch(ctx, execute_permit)
