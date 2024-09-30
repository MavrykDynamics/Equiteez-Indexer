from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage
from equiteez.utils.utils import persist_lambda

async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, OrderbookStorage],
) -> None:
    # Persist lambda
    await persist_lambda(models.Orderbook, models.OrderbookLambda, set_lambda)
