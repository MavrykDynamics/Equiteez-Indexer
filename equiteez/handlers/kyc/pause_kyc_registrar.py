from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.pause_kyc_registrar import (
    PauseKycRegistrarParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def pause_kyc_registrar(
    ctx: HandlerContext,
    pause_kyc_registrar: TezosTransaction[PauseKycRegistrarParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, pause_kyc_registrar)
