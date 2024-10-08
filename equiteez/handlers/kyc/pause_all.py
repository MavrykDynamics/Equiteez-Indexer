from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.pause_all import PauseAllParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def pause_all(
    ctx: HandlerContext,
    pause_all: TezosTransaction[PauseAllParameter, KycStorage],
) -> None:
    breakpoint()