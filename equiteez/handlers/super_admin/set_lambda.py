from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, SuperAdminStorage],
) -> None:
    # Persist lambda
    await persist_lambda(models.SuperAdmin, models.SuperAdminLambda, set_lambda)
