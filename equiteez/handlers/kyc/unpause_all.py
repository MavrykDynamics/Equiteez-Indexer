from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.unpause_all import UnpauseAllParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def unpause_all(
    ctx: HandlerContext,
    unpause_all: TezosTransaction[UnpauseAllParameter, KycStorage],
) -> None:
    breakpoint()