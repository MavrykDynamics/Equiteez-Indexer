from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_registrar_admin import (
    SetRegistrarAdminParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_registrar_admin(
    ctx: HandlerContext,
    set_registrar_admin: TezosTransaction[SetRegistrarAdminParameter, KycStorage],
) -> None:
    # The registrar is the caller; admins are added or removed in
    # kycAdminRegistrarLedger
    await sync_kyc_operation(ctx, set_registrar_admin)
