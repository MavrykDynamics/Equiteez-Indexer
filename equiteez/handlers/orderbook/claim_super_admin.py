from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.claim_super_admin import ClaimSuperAdminParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def claim_super_admin(
    ctx: HandlerContext,
    claim_super_admin: TezosTransaction[ClaimSuperAdminParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address         = claim_super_admin.data.target_address
    new_super_admin = claim_super_admin.storage.newSuperAdmin
    super_admin     = claim_super_admin.storage.superAdmin

    # Update orderbook
    orderbook       = await models.Orderbook.get(
        address = address
    )
    orderbook.new_super_admin   = new_super_admin
    orderbook.super_admin       = super_admin
    await orderbook.save()
