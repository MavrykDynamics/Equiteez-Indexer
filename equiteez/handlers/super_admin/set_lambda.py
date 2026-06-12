from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action, persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, SuperAdminStorage],
) -> None:
    # Record signatory action (multisig path)
    await create_super_admin_action(set_lambda)

    # Persist lambda when it was applied directly (bootstrap path)
    if set_lambda.parameter.name in set_lambda.storage.lambdaLedger:
        await persist_lambda(models.SuperAdmin, models.SuperAdminLambda, set_lambda)
