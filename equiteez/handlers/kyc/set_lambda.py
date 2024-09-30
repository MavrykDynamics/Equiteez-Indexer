from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.utils import persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, KycStorage],
) -> None:
    # Persist lambda
    await persist_lambda(models.Kyc, models.KycLambda, set_lambda)
