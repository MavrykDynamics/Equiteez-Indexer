from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.claim_super_admin import (
    ClaimSuperAdminParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, claim_super_admin)
