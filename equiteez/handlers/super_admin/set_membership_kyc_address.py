from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_membership_kyc_address import (
    SetMembershipKycAddressParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_membership_kyc_address(
    ctx: HandlerContext,
    set_membership_kyc_address: TezosTransaction[
        SetMembershipKycAddressParameter, SuperAdminStorage
    ],
) -> None:
    # Only creates a PENDING action; the targets' %setMembershipKycAddress calls
    # are emitted once the action executes via signAction
    await create_super_admin_action(set_membership_kyc_address)
