from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.kyc.tezos_parameters.set_membership_tier_discount import (
    SetMembershipTierDiscountParameter,
)
from equiteez.types.kyc.tezos_storage import KycStorage


async def set_membership_tier_discount(
    ctx: HandlerContext,
    set_membership_tier_discount: TezosTransaction[
        SetMembershipTierDiscountParameter, KycStorage
    ],
) -> None:
    # Fetch operation info
    address = set_membership_tier_discount.data.target_address

    # Get kyc
    kyc = await models.Kyc.get(address=address)

    # Update records
    for item in set_membership_tier_discount.parameter.root:
        if item.updateType == "remove":
            await models.KycMembershipTierDiscount.filter(
                kyc=kyc,
                membership_tier=item.membershipTierName,
                discount_name=item.discountName,
            ).delete()
        else:
            discount, _ = await models.KycMembershipTierDiscount.get_or_create(
                kyc=kyc,
                membership_tier=item.membershipTierName,
                discount_name=item.discountName,
            )
            discount.discount_value = int(item.discountValue)
            await discount.save()
