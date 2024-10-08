from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.marketplace.tezos_parameters.set_lambda import SetLambdaParameter
from equiteez.types.marketplace.tezos_storage import MarketplaceStorage
from equiteez.utils.utils import persist_lambda


async def set_lambda(
    ctx: HandlerContext,
    set_lambda: TezosTransaction[SetLambdaParameter, MarketplaceStorage],
) -> None:
    # Persist lambda
    await persist_lambda(models.Marketplace, models.MarketplaceLambda, set_lambda)
