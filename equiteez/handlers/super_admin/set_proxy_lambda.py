from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_proxy_lambda import (
    SetProxyLambdaParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_proxy_lambda(
    ctx: HandlerContext,
    set_proxy_lambda: TezosTransaction[SetProxyLambdaParameter, SuperAdminStorage],
) -> None:
    # The lambda name / bytes / target contract address are captured in the
    # action data map; the lambda is only forwarded to the target contract
    # once the action is executed via signAction, where it is indexed by the
    # target contract setLambda handler
    await create_super_admin_action(set_proxy_lambda)
