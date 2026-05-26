from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction

from equiteez import models as models
from equiteez.types.launchpad.tezos_parameters.set_membership_kyc_address import (
    SetMembershipKycAddressParameter,
)
from equiteez.types.launchpad.tezos_storage import LaunchpadStorage


async def set_membership_kyc_address(
    ctx: HandlerContext,
    set_membership_kyc_address: TezosTransaction[
        SetMembershipKycAddressParameter, LaunchpadStorage
    ],
) -> None:
    address = set_membership_kyc_address.data.target_address
    new_kyc_address = set_membership_kyc_address.storage.membershipKycAddress

    launchpad = await models.Launchpad.get(address=address)
    kyc, _ = await models.Kyc.get_or_create(address=new_kyc_address)
    await kyc.save()
    launchpad.membership_kyc = kyc
    await launchpad.save()
