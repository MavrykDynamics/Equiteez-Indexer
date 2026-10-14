from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_enable_membership import (
    SetEnableMembershipParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_enable_membership(
    ctx: HandlerContext,
    set_enable_membership: TezosTransaction[SetEnableMembershipParameter, KycStorage],
) -> None:
    await sync_kyc_operation(ctx, set_enable_membership)
