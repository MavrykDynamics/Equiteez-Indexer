from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.set_token_kyc_address import (
    SetTokenKycAddressParameter,
)
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action


async def set_token_kyc_address(
    ctx: HandlerContext,
    set_token_kyc_address: TezosTransaction[
        SetTokenKycAddressParameter, SuperAdminStorage
    ],
) -> None:
    await create_super_admin_action(set_token_kyc_address)
