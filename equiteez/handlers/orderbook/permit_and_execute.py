from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.permit_and_execute import (
    PermitAndExecuteParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.orderbook_utils import record_permit_batch


async def permit_and_execute(
    ctx: HandlerContext,
    permit_and_execute: TezosTransaction[PermitAndExecuteParameter, OrderbookStorage],
) -> None:
    await record_permit_batch(ctx, permit_and_execute)
