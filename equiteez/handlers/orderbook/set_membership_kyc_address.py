from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_membership_kyc_address import (
    SetMembershipKycAddressParameter,
)
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def set_membership_kyc_address(
    ctx: HandlerContext,
    set_membership_kyc_address: TezosTransaction[
        SetMembershipKycAddressParameter, OrderbookStorage
    ],
) -> None:
    # Fetch operations info
    address = set_membership_kyc_address.data.target_address
    kyc_address = set_membership_kyc_address.storage.membershipKycAddress

    # Get orderbook
    orderbook = await models.Orderbook.get(address=address)

    # Update record
    kyc, _ = await models.Kyc.get_or_create(address=kyc_address)
    orderbook.kyc = kyc
    await orderbook.save()
