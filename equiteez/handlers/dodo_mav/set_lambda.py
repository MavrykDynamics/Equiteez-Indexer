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
    dodo_mav = await models.DodoMav.get_or_none(address=set_lambda.data.target_address)
    if not dodo_mav:
        return
    await persist_lambda(models.DodoMav, models.DodoMavLambda, set_lambda)
