from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_whitelist import SetWhitelistParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_whitelist(
    ctx: HandlerContext,
    set_whitelist: TezosTransaction[SetWhitelistParameter, KycStorage],
) -> None:
    breakpoint()