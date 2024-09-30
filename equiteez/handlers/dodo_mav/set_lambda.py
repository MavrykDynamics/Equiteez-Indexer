from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.dodo_mav.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.dodo_mav.tezos_storage import DodoMavStorage
from equiteez.utils.utils import persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, DodoMavStorage],
) -> None:
    # Persist lambda
    await persist_lambda(models.DodoMav, models.DodoMavLambda, set_lambda)
