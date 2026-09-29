from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_membership_tier import (
    SetMembershipTierParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_membership_tier(
    ctx: HandlerContext,
    set_membership_tier: TezosTransaction[SetMembershipTierParameter, KycStorage],
) -> None:
    # Removing a tier also drops its discounts but keeps member assignments
    await sync_kyc_operation(ctx, set_membership_tier)
