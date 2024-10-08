from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_blacklist import SetBlacklistParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_blacklist(
    ctx: HandlerContext,
    set_blacklist: TezosTransaction[SetBlacklistParameter, KycStorage],
) -> None:
    breakpoint()