from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_kyc_registrar import (
    SetKycRegistrarParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_kyc_registrar(
    ctx: HandlerContext,
    set_kyc_registrar: TezosTransaction[SetKycRegistrarParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_kyc_registrar)
