from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage
from equiteez.utils.utils import persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, LaunchpadStorage],
) -> None:
    await persist_lambda(models.Launchpad, models.LaunchpadLambda, set_lambda)
