from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.orderbook.tezos_parameters.set_super_admin import SetSuperAdminParameter
from equiteez.types.orderbook.tezos_storage import OrderbookStorage


async def set_super_admin(
    ctx: HandlerContext,
    set_super_admin: TezosTransaction[SetSuperAdminParameter, OrderbookStorage],
) -> None:
    # Fetch operation info
    address         = set_super_admin.data.target_address
    new_super_admin = set_super_admin.storage.newSuperAdmin

    # Update orderbook
    orderbook       = await models.Orderbook.get(
        address = address
    )
    orderbook.new_super_admin   = new_super_admin
    await orderbook.save()
    