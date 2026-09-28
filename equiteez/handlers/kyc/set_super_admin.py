from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_super_admin import SetSuperAdminParameter
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_super_admin)
