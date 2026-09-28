from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez.types.kyc.tezos_parameters.set_membership_tier_discount import (
    SetMembershipTierDiscountParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage
from equiteez.utils.kyc_utils import sync_kyc_operation


async def set_membership_tier_discount(
    ctx: HandlerContext,
    set_membership_tier_discount: TezosTransaction[
        SetMembershipTierDiscountParameter, KycStorage
    ],
) -> None:
    await sync_kyc_operation(ctx, set_membership_tier_discount)
