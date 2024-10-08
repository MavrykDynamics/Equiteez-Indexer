from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.pause_kyc_registrar import PauseKycRegistrarParameter
from equiteez.types.kyc.tezos_storage import KycStorage


async def pause_kyc_registrar(
    ctx: HandlerContext,
    pause_kyc_registrar: TezosTransaction[PauseKycRegistrarParameter, KycStorage],
) -> None:
    breakpoint()